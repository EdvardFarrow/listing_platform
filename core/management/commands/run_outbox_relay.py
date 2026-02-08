import asyncio
import logging

from decouple import config
from django.core.management.base import BaseCommand
from django.db import transaction
from faststream.kafka import KafkaBroker

from core.models import OutboxEvent

BATCH_SIZE = 100
POLL_INTERVAL = 0.5
BROKER_URL = config("BROKER_URL")

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Reads events from Outbox table and pushes them to redpanda"

    def handle(self, *args, **options):
        asyncio.run(self.run_relay())

    async def run_relay(self):
        logger.info("Starting Outbox Relay...")

        broker = KafkaBroker(BROKER_URL)
        await broker.connect()

        try:
            while True:
                events_to_process = await self.fetch_events()

                if not events_to_process:
                    await asyncio.sleep(POLL_INTERVAL)
                    continue

                logger.info(f"Found {len(events_to_process)} events. Processing...")

                successful_ids = []
                for event in events_to_process:
                    try:
                        await broker.publish(
                            event.payload,
                            topic=event.topic
                        )
                        successful_ids.append(event.id)
                    except Exception as e:
                        logger.error(f"Failed to publish event {event.id}: {e}")
                        event.error_log = str(e)
                        await event.asave()

                if successful_ids:
                    await self.cleanup_events(successful_ids)
                    logger.info(f"Successfully processed {len(successful_ids)} events")

        except KeyboardInterrupt:
            logger.info("Stopping relay...")
        finally:
            await broker.disconnect()


    @transaction.atomic
    def fetch_events_sync(self):
        events = list(
            OutboxEvent.objects.filter(processed=False)
            .select_for_update(skip_locked=True)
            .order_by('created_at')[:BATCH_SIZE]
        )
        return events

    async def fetch_events(self):
        return await asyncio.to_thread(self.fetch_events_sync)

    async def cleanup_events(self, ids):
        await OutboxEvent.objects.filter(id__in=ids).adelete()
