import base64
import hashlib
import hmac
import logging
from typing import Any, Dict

from fastapi import HTTPException, Request, status

from eyos.config import Settings
from eyos.models import NewStoreEvent
from eyos.services.hail_client import HailClient
from eyos.services.transformer import transform_newstore_to_hail

logger = logging.getLogger(__name__)


class NewStoreWebhookHandler:
    """Handler for NewStore webhooks."""

    def __init__(self, settings: Settings, hail_client: HailClient):
        """
        Initialize the webhook handler.

        Args:
            settings: Application settings
            hail_client: Client for the Hail API
        """
        self.webhook_secret = settings.newstore_webhook_secret
        self.supported_events = settings.newstore_supported_events
        self.hail_client = hail_client

    async def validate_signature(self, request: Request, body: bytes) -> None:
        """
        Validate the webhook signature.

        Args:
            request: The incoming HTTP request
            body: The raw request body

        Raises:
            HTTPException: When the signature is invalid
        """
        # Skip validation in mock mode
        if self.webhook_secret == "mock_webhook_secret":
            return

        # In a real implementation, NewStore would send a signature header
        signature_header = request.headers.get("X-NewStore-Signature")
        if not signature_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing signature header"
            )

        # Calculate the expected signature
        expected_signature = hmac.new(
            key=self.webhook_secret.encode(),
            msg=body,
            digestmod=hashlib.sha256
        ).digest()
        expected_signature_b64 = base64.b64encode(expected_signature).decode()

        # Compare signatures (use constant-time comparison to prevent timing attacks)
        if not hmac.compare_digest(signature_header, expected_signature_b64):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature"
            )

    async def validate_event(self, event: NewStoreEvent) -> None:
        """
        Validate the webhook event.

        Args:
            event: The webhook event to validate

        Raises:
            HTTPException: When the event is invalid
        """
        if event.name not in self.supported_events:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported event type: {event.name}"
            )

        # Validate required fields
        if not event.payload.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing order ID"
            )

        if not event.payload.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order must have at least one item"
            )

        # Additional validation could be added here
        logger.info(f"Validated {event.name} event for order {event.payload.id}")

    async def process_event(self, event: NewStoreEvent) -> Dict[str, Any]:
        """
        Process the webhook event.

        Args:
            event: The webhook event to process

        Returns:
            Metadata about the processed event

        Raises:
            HTTPException: When processing fails
        """
        logger.info(f"Processing {event.name} event for order {event.payload.id}")

        try:
            # Transform the NewStore event to a Hail transaction
            hail_transaction = await transform_newstore_to_hail(event)

            # Send the transaction to the Hail API
            result = await self.hail_client.send_transaction(hail_transaction)

            return {
                "event_id": event.payload.id,
                "event_type": event.name,
                "tenant": event.tenant,
                "status": "processed",
                "transaction_id": hail_transaction.receipt.transaction_information.id,
                "hail_response": result
            }
        except Exception as e:
            logger.error(f"Error processing event: {e!s}")
            raise HTTPException(
                status_code=500,
                detail=f"Error processing event: {e!s}"
            ) from e
