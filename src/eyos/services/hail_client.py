import asyncio
import json
import logging
from typing import Any, Dict

import httpx
from fastapi import HTTPException

from eyos.config import Settings
from eyos.models import HailTransaction

logger = logging.getLogger(__name__)


class HailClient:
    """Client for interacting with the Hail API."""

    def __init__(self, settings: Settings):
        """
        Initialize the Hail API client.

        Args:
            settings: Application settings including API configuration
        """
        self.base_url = settings.hail_api_base_url
        self.api_key = settings.hail_api_key
        self.max_retries = settings.hail_api_max_retries
        self.retry_delay = settings.hail_api_retry_delay

    async def send_transaction(
        self,
        transaction: HailTransaction,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Send a transaction to the Hail API with retry logic.

        Args:
            transaction: The transaction to send
            retry_count: Current retry attempt

        Returns:
            The API response

        Raises:
            HTTPException: When the API request fails after all retries
        """
        if retry_count > self.max_retries:
            error_msg = f"Failed to send transaction to Hail API after {self.max_retries} retries"
            logger.error(error_msg)
            raise HTTPException(status_code=503, detail=error_msg)

        try:
            # In a real implementation, we would use the actual API URL
            # For this mock, we'll simulate a successful response
            if self.base_url == "mock":
                # Simulate occasional failure for testing retry logic
                if retry_count == 0 and asyncio.get_event_loop().time() % 3 == 0:
                    raise httpx.ConnectTimeout("Simulated connection timeout")

                # Simulate a successful response
                logger.info(f"Successfully sent transaction to Hail API: {transaction.receipt.transaction_information.id}")
                result: Dict[str, Any] = {
                    "status": "success",
                    "transaction_id": transaction.receipt.transaction_information.id,
                    "message": "Transaction processed successfully"
                }
                return result

            # In a real implementation:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/events/v2/transaction/",
                    headers=headers,
                    json=json.loads(transaction.model_dump_json())
                )

                response.raise_for_status()
                result_data: Dict[str, Any] = response.json()
                return result_data

        except (httpx.ConnectTimeout, httpx.ConnectError, httpx.ReadTimeout) as e:
            # Network-related errors - retryable
            logger.warning(
                f"Temporary connection error when sending to Hail API: {e!s}. "
                f"Retrying {retry_count + 1}/{self.max_retries}"
            )
            # Exponential backoff with jitter
            delay = self.retry_delay * (2 ** retry_count) * (0.5 + asyncio.get_event_loop().time() % 1)
            await asyncio.sleep(delay)
            return await self.send_transaction(transaction, retry_count + 1)

        except httpx.HTTPStatusError as e:
            # Server errors (5xx) are retryable, client errors (4xx) are not
            if 500 <= e.response.status_code < 600:
                logger.warning(
                    f"Hail API server error: {e.response.status_code}. "
                    f"Retrying {retry_count + 1}/{self.max_retries}"
                )
                await asyncio.sleep(self.retry_delay * (2 ** retry_count))
                return await self.send_transaction(transaction, retry_count + 1)
            else:
                error_msg = f"Hail API client error: {e.response.status_code} - {e.response.text}"
                logger.error(error_msg)
                raise HTTPException(status_code=e.response.status_code, detail=error_msg) from e

        except Exception as e:
            # Unexpected errors
            error_msg = f"Unexpected error when sending to Hail API: {e!s}"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg) from e
