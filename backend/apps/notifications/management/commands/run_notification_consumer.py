"""
Management command to run the Notification Kafka consumer.

Usage
-----
  python manage.py run_notification_consumer

Run this as a long-lived process in Docker/K8s alongside your web workers.
It polls Kafka, handles events, and persists+dispatches notifications.

Graceful shutdown is handled via SIGTERM / SIGINT (Ctrl-C).
"""
from __future__ import annotations

import logging
import signal

from django.core.management.base import BaseCommand

from apps.notifications.constants import (
    NOTIFICATION_CONSUMER_GROUP_ID,
    NOTIFICATION_CONSUMER_POLL_TIMEOUT,
    NOTIFICATION_CONSUMER_TOPICS,
)
from apps.notifications.events import handle_kafka_event
from core.kafka.consumer import BaseKafkaConsumer

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Run the Notification domain Kafka consumer (long-running process)"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._running = True

    def handle(self, *args, **options):
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)

        consumer = BaseKafkaConsumer(
            topics=NOTIFICATION_CONSUMER_TOPICS,
            group_id=NOTIFICATION_CONSUMER_GROUP_ID,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Notification consumer started\n"
                f"    Topics : {NOTIFICATION_CONSUMER_TOPICS}\n"
                f"    Group  : {NOTIFICATION_CONSUMER_GROUP_ID}"
            )
        )

        try:
            while self._running:
                msg = consumer.poll(timeout=NOTIFICATION_CONSUMER_POLL_TIMEOUT)

                if msg is None:
                    continue

                if msg.error():
                    logger.error(
                        "kafka.consumer.error",
                        extra={"error": str(msg.error())},
                    )
                    continue

                logger.debug(
                    "kafka.event.received",
                    extra={
                        "topic": msg.topic(),
                        "partition": msg.partition(),
                        "offset": msg.offset(),
                    },
                )

                handle_kafka_event(topic=msg.topic(), value=msg.value())

        except Exception as exc:
            logger.critical(
                "kafka.consumer.fatal",
                extra={"error": str(exc)},
            )
            self.stderr.write(self.style.ERROR(f"Fatal: {exc}"))
            raise

        finally:
            consumer.close()
            self.stdout.write(self.style.WARNING("Notification consumer stopped"))

    def _handle_shutdown(self, signum, frame) -> None:
        self.stdout.write(self.style.WARNING("Shutdown signal received - finishing current message..."))
        self._running = False
