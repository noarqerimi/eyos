import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Awaitable, Callable, Dict, Optional, Union

from eyos.config import Settings
from eyos.models import NewStoreEvent
from eyos.services.hail_client import HailClient
from eyos.services.transformer import transform_newstore_to_hail

logger = logging.getLogger(__name__)


class InMemoryQueue:
    """
    In-memory queue for background processing.

    In a production environment, this would be replaced with a proper message queue
    like RabbitMQ, AWS SQS, or Redis.
    """

    def __init__(self) -> None:
        """Initialize the in-memory queue."""
        self.queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        self.running = False
        self.task: Optional[asyncio.Task[None]] = None

    async def enqueue(self, event: Dict[str, Any]) -> None:
        """
        Add an event to the queue.

        Args:
            event: The event to enqueue
        """
        await self.queue.put(event)
        logger.info(f"Enqueued event with ID: {event.get('payload', {}).get('id', 'unknown')}")

    async def process_queue(
        self,
        processor: Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> None:
        """
        Process items from the queue.

        Args:
            processor: Callback function to process each item
        """
        while self.running:
            try:
                # Wait for an item with a timeout to allow for graceful shutdown
                try:
                    item = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                # Process the item
                try:
                    await processor(item)
                except Exception as e:
                    logger.error(f"Error processing queue item: {e!s}")
                finally:
                    self.queue.task_done()

            except asyncio.CancelledError:
                logger.info("Queue processor task was cancelled")
                break
            except Exception as e:
                logger.error(f"Unexpected error in queue processor: {e!s}")
                # Avoid tight loop if there's a persistent error
                await asyncio.sleep(1)

    async def start(
        self,
        processor: Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> None:
        """
        Start processing the queue.

        Args:
            processor: Callback function to process each item
        """
        if self.running:
            return

        self.running = True
        self.task = asyncio.create_task(self.process_queue(processor))
        logger.info("Queue processor started")

    async def stop(self) -> None:
        """Stop processing the queue."""
        if not self.running:
            return

        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Queue processor stopped")


class QueueProcessor:
    """
    Processor for handling queued events.

    This service is responsible for:
    1. Taking events from the queue
    2. Transforming NewStore events to Hail API format
    3. Sending the transformed events to the Hail API
    """

    def __init__(self, queue: InMemoryQueue, settings: Settings) -> None:
        """
        Initialize the queue processor.

        Args:
            queue: Queue for event processing
            settings: Application settings
        """
        self.settings = settings
        self.queue = queue

        # Get HailClient from settings
        self.hail_client = HailClient(settings)

    @asynccontextmanager
    async def lifespan(self) -> AsyncGenerator[None, None]:
        """Lifecycle manager for the queue processor."""
        await self.queue.start(self.process_event)
        try:
            yield
        finally:
            await self.queue.stop()

    async def enqueue_event(self, event: Union[Dict[str, Any], NewStoreEvent]) -> None:
        """
        Enqueue an event for processing.

        Args:
            event: The event to enqueue (either a dict or NewStoreEvent)
        """
        # Convert to dict for serialization if it's a Pydantic model
        if isinstance(event, NewStoreEvent):
            event_dict = json.loads(event.model_dump_json())
        else:
            event_dict = event

        await self.queue.enqueue(event_dict)

    async def process_event(self, event_dict: Dict[str, Any]) -> None:
        """
        Process a single event from the queue.

        Args:
            event_dict: The event to process
        """
        try:
            # Parse the event
            event = NewStoreEvent.model_validate(event_dict)
            logger.info(
                f"Processing queued event: {event.name} for order {event.payload.id}"
            )

            # Transform the event to Hail API format
            hail_transaction = await transform_newstore_to_hail(event)

            # Send the transformed event to the Hail API
            response = await self.hail_client.send_transaction(hail_transaction)

            logger.info(
                f"Successfully processed event: {event.name} for order {event.payload.id}. "
                f"Hail API response: {response.get('status', 'unknown')}"
            )

        except Exception as e:
            logger.error(f"Error processing event from queue: {e!s}")
            # In a production environment, we would:
            # 1. Implement a dead-letter queue for failed events
            # 2. Track retry counts per event
            # 3. Apply more sophisticated retry strategies
