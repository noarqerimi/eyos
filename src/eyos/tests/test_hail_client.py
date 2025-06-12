from unittest.mock import MagicMock, patch

import httpx
import pytest
from fastapi import HTTPException

from eyos.config import Settings
from eyos.models.hail import HailTransaction, Receipt, TransactionInfo
from eyos.services.hail_client import HailClient


@pytest.fixture
def settings() -> Settings:
    """Create test settings."""
    return Settings(
        hail_api_base_url="mock",
        hail_api_key="test_key",
        hail_api_max_retries=2,
        hail_api_retry_delay=0.1
    )


@pytest.fixture
def mock_transaction() -> HailTransaction:
    """Create a mock transaction."""
    # Create a minimal transaction for testing
    transaction = MagicMock(spec=HailTransaction)
    transaction.receipt = MagicMock(spec=Receipt)
    transaction.receipt.transaction_information = MagicMock(spec=TransactionInfo)
    transaction.receipt.transaction_information.id = "test-transaction-id"
    transaction.model_dump_json.return_value = '{"test": "data"}'
    return transaction


@pytest.mark.asyncio
async def test_send_transaction_success(settings: Settings, mock_transaction: HailTransaction) -> None:
    """Test successful transaction sending."""
    client = HailClient(settings)

    # Test the mock mode (which should always succeed)
    response = await client.send_transaction(mock_transaction)

    assert response["status"] == "success"
    assert response["transaction_id"] == "test-transaction-id"


@pytest.mark.asyncio
async def test_send_transaction_retry_timeout(settings: Settings, mock_transaction: HailTransaction) -> None:
    """Test transaction retry on timeout."""
    # Override settings to use a real URL for testing retries
    settings.hail_api_base_url = "https://api.example.com"
    client = HailClient(settings)

    # Create mock responses
    mock_success = MagicMock()
    mock_success.raise_for_status.return_value = None
    mock_success.json.return_value = {"status": "success"}

    # Mock the httpx client to simulate a timeout
    with patch("httpx.AsyncClient.post") as mock_post:
        # Configure mocks
        mock_post.side_effect = [
            httpx.ConnectTimeout("Connection timed out"),
            mock_success  # Second call succeeds
        ]

        response = await client.send_transaction(mock_transaction)

        # Verify that we got a successful response after retry
        assert response["status"] == "success"
        assert mock_post.call_count == 2


@pytest.mark.asyncio
async def test_send_transaction_retry_server_error(settings: Settings, mock_transaction: HailTransaction) -> None:
    """Test transaction retry on server error."""
    # Override settings to use a real URL for testing retries
    settings.hail_api_base_url = "https://api.example.com"
    client = HailClient(settings)

    # Create mock responses
    error_response = MagicMock()
    error_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Server error",
        request=httpx.Request("POST", "https://api.example.com"),
        response=MagicMock(status_code=500, text="Internal server error")
    )

    success_response = MagicMock()
    success_response.raise_for_status.return_value = None
    success_response.json.return_value = {"status": "success"}

    # Mock the httpx client to simulate a 500 error followed by success
    with patch("httpx.AsyncClient.post") as mock_post:
        # Configure mock
        mock_post.side_effect = [error_response, success_response]

        response = await client.send_transaction(mock_transaction)

        # Verify that we got a successful response after retry
        assert response["status"] == "success"
        assert mock_post.call_count == 2


@pytest.mark.asyncio
async def test_send_transaction_client_error(settings: Settings, mock_transaction: HailTransaction) -> None:
    """Test transaction handling of client errors (no retry)."""
    # Override settings to use a real URL for testing
    settings.hail_api_base_url = "https://api.example.com"
    client = HailClient(settings)

    # Mock the httpx client to simulate a 400 error
    with patch("httpx.AsyncClient.post") as mock_post:
        # Create mock response
        error_response = MagicMock()
        http_error = httpx.HTTPStatusError(
            "Client error",
            request=httpx.Request("POST", "https://api.example.com"),
            response=MagicMock(status_code=400, text="Bad request")
        )
        error_response.raise_for_status.side_effect = http_error

        mock_post.return_value = error_response

        # Should raise an HTTPException without retrying
        with pytest.raises(HTTPException) as excinfo:
            await client.send_transaction(mock_transaction)

        assert excinfo.value.status_code == 400
        assert mock_post.call_count == 1


@pytest.mark.asyncio
async def test_send_transaction_max_retries_exceeded(settings: Settings, mock_transaction: HailTransaction) -> None:
    """Test transaction handling when max retries are exceeded."""
    # Override settings to use a real URL and low retry count
    settings.hail_api_base_url = "https://api.example.com"
    settings.hail_api_max_retries = 1
    client = HailClient(settings)

    # Mock the httpx client to simulate persistent timeouts
    with patch("httpx.AsyncClient.post") as mock_post:
        # Both calls raise timeouts
        mock_post.side_effect = httpx.ConnectTimeout("Connection timed out")

        # Should raise an HTTPException after retries are exhausted
        with pytest.raises(HTTPException) as excinfo:
            await client.send_transaction(mock_transaction)

        assert excinfo.value.status_code == 503
        assert "Failed to send transaction to Hail API after 1 retries" in excinfo.value.detail
        assert mock_post.call_count == 2  # Initial + 1 retry
