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

from django.core.management.base import BaseCommand

from apps.notifications.constants import (
    NOTIFICATION_CONSUMER_GROUP_ID,
    NOTIFICATION_CONSUMER_TOPICS,
)
from apps.notifications.events import handle_kafka_event
from core.kafka.consumer import BaseKafkaConsumer

logger = logging.getLogger(__name__)


class NotificationKafkaConsumer(BaseKafkaConsumer):
    """Kafka consumer implementation for notifications domain events."""

    topics = NOTIFICATION_CONSUMER_TOPICS

    def handle_message(self, topic: str, event_data: dict) -> None:
        handle_kafka_event(topic=topic, value=event_data)


class Command(BaseCommand):
    help = "Run the Notification domain Kafka consumer (long-running process)"

    def handle(self, *args, **options):
        consumer = NotificationKafkaConsumer(group_id=NOTIFICATION_CONSUMER_GROUP_ID)

        self.stdout.write(
            self.style.SUCCESS(
                f"Notification consumer started\n"
                f"    Topics : {NOTIFICATION_CONSUMER_TOPICS}\n"
                f"    Group  : {NOTIFICATION_CONSUMER_GROUP_ID}"
            )
        )

        try:
            consumer.start()

        except Exception as exc:
            logger.critical(
                "kafka.consumer.fatal",
                extra={"error": str(exc)},
            )
            self.stderr.write(self.style.ERROR(f"Fatal: {exc}"))
            raise

        finally:
            consumer.stop()
            self.stdout.write(self.style.WARNING("Notification consumer stopped"))
