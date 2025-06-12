import logging
from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Request

from eyos.config import Settings, get_settings
from eyos.models.newstore import NewStoreEvent
from eyos.services.hail_client import HailClient
from eyos.services.newstore_webhook import NewStoreWebhookHandler
from eyos.services.queue_processor import InMemoryQueue, QueueProcessor

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/webhooks/newstore",
    tags=["webhooks"],
    responses={
        404: {"description": "Not found"},
        400: {"description": "Bad request"},
        500: {"description": "Internal server error"},
        202: {"description": "Accepted for processing"},
    }
)


def get_webhook_handler() -> NewStoreWebhookHandler:
    """Dependency for the webhook handler."""
    settings = get_settings()
    hail_client = HailClient(settings)
    return NewStoreWebhookHandler(settings, hail_client)


def get_queue_processor() -> QueueProcessor:
    """Dependency for the queue processor."""
    settings = get_settings()
    queue = InMemoryQueue()
    return QueueProcessor(queue, settings)


@router.post(
    "/",
    status_code=202,
    summary="Process NewStore webhook event",
)
async def process_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    event: NewStoreEvent = Body(...),
    webhook_handler: NewStoreWebhookHandler = Depends(get_webhook_handler),
    queue_processor: QueueProcessor = Depends(get_queue_processor),
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Process a webhook event from NewStore.

    This endpoint accepts events from NewStore's webhook system and
    processes them asynchronously. The event is validated and transformed
    into a format suitable for the Hail API.

    Args:
        request: The HTTP request
        background_tasks: FastAPI's background tasks
        event: The webhook event from NewStore
        webhook_handler: Service for handling webhook events
        queue_processor: Service for processing events in background
        settings: Application settings

    Returns:
        A dictionary with the status of the request
    """
    # Validate the event
    try:
        await webhook_handler.validate_event(event)
    except Exception as e:
        logger.info(
            f"Validation failed for {event.name} event for order {event.payload.id}: {e!s}"
        )
        raise HTTPException(status_code=400, detail=f"Invalid event: {e!s}") from e

    # Use the queue for async processing if enabled
    if settings.queue_enabled:
        # Add the event to the queue for processing
        await queue_processor.enqueue_event(event.dict())

        return {
            "status": "accepted",
            "message": f"Event '{event.name}' for order {event.payload.id} accepted for processing",
            "queued": True
        }
    else:
        # Process the event directly
        try:
            result = await webhook_handler.process_event(event)

            logger.info(
                f"Successfully processed {event.name} event for order {event.payload.id}"
            )

            return {
                "status": "processed",
                "message": f"Event '{event.name}' for order {event.payload.id} processed successfully",
                "queued": False,
                "result": result
            }
        except Exception as e:
            logger.error(f"Error processing event directly: {e!s}")
            raise HTTPException(
                status_code=500,
                detail=f"Error processing event: {e!s}"
            ) from e


@router.post(
    "/simulate",
    status_code=202,
    summary="Simulate a NewStore webhook event",
)
async def simulate_webhook(
    background_tasks: BackgroundTasks,
    event: NewStoreEvent = Body(...),
    webhook_handler: NewStoreWebhookHandler = Depends(get_webhook_handler),
    queue_processor: QueueProcessor = Depends(get_queue_processor),
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Simulate a webhook event from NewStore.

    This endpoint behaves the same as the main webhook endpoint, but is intended
    for testing and development. It accepts the same event format and processes
    it the same way.

    Args:
        background_tasks: FastAPI's background tasks
        event: The webhook event from NewStore
        webhook_handler: Service for handling webhook events
        queue_processor: Service for processing events in background
        settings: Application settings

    Returns:
        A dictionary with the status of the request
    """
    logger.info(
        f"Simulating {event.name} event for order {event.payload.id}"
    )

    # Process the same as a real webhook
    return await process_webhook(
        request=Request(scope={"type": "http"}),  # Create a minimal request
        background_tasks=background_tasks,
        event=event,
        webhook_handler=webhook_handler,
        queue_processor=queue_processor,
        settings=settings
    )
