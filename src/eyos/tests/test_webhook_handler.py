import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from eyos.config import Settings
from eyos.main import app
from eyos.models.newstore import NewStoreEvent
from eyos.services.newstore_webhook import NewStoreWebhookHandler
from eyos.services.hail_client import HailClient


@pytest.fixture
def sample_newstore_event():
    """Load sample NewStore event data."""
    sample_file = Path(__file__).parent.parent.parent.parent / "newstore_sample_payload.json"
    with open(sample_file, "r") as f:
        data = json.load(f)
    return NewStoreEvent(**data)


@pytest.fixture
def webhook_handler():
    """Create a webhook handler with mock settings."""
    settings = Settings(
        newstore_webhook_secret="test_secret",
        newstore_supported_events=["order.completed"],
        hail_api_base_url="mock",
        hail_api_key="test_key"
    )
    hail_client = HailClient(settings)
    return NewStoreWebhookHandler(settings, hail_client)


@pytest.mark.asyncio
async def test_validate_event_success(webhook_handler, sample_newstore_event):
    """Test successful event validation."""
    # Should not raise an exception
    await webhook_handler.validate_event(sample_newstore_event)


@pytest.mark.asyncio
async def test_validate_event_unsupported_type(webhook_handler, sample_newstore_event):
    """Test validation of an unsupported event type."""
    # Modify the event type
    sample_newstore_event.name = "order.created"

    # Should raise an exception
    with pytest.raises(HTTPException) as excinfo:
        await webhook_handler.validate_event(sample_newstore_event)

    assert excinfo.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "Unsupported event type" in excinfo.value.detail


@pytest.mark.asyncio
async def test_process_event(webhook_handler, sample_newstore_event):
    """Test event processing."""
    # Call the method directly without mocking to use the real implementation
    result = await webhook_handler.process_event(sample_newstore_event)
    
    # Verify the result
    assert result["event_id"] == sample_newstore_event.payload.id
    assert result["event_type"] == sample_newstore_event.name
    assert result["status"] == "processed"
    assert "transaction_id" in result
    assert result["transaction_id"].startswith("TRX-newlook-")
    assert "hail_response" in result
    assert result["hail_response"]["status"] == "success"


@pytest.mark.skip("Integration test - requires running server")
def test_webhook_endpoint():
    """Test the webhook endpoint."""
    # Create a test client
    client = TestClient(app)

    # Mock the background tasks
    with patch("fastapi.BackgroundTasks.add_task", return_value=None) as mock_add_task:
        # Load the sample event
        sample_file = Path(__file__).parent.parent.parent.parent / "newstore_sample_payload.json"
        with open(sample_file, "r") as f:
            data = json.load(f)

        # Send a POST request to the webhook endpoint
        response = client.post(
            "/webhooks/newstore/simulate",
            json=data
        )

        # Validate the response
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert "event_id" in response.json()
        assert "event_type" in response.json()
        assert "status" in response.json()
