"""
core/kafka/consumer.py
~~~~~~~~~~~~~~~~~~~~~~
Base Kafka consumer class.

Each app that needs to consume events subclasses BaseKafkaConsumer
and implements handle_message().

Usage (in an app's management command or worker)
------------------------------------------------
    from core.kafka.consumer import BaseKafkaConsumer
    from core.kafka.topics import Topics

    class FeedConsumer(BaseKafkaConsumer):
        topics = [Topics.POST_CREATED, Topics.USER_FOLLOWED]

        def handle_message(self, topic: str, event_data: dict) -> None:
            if topic == Topics.POST_CREATED:
                fanout_service.fanout_post(event_data["post_id"])

    consumer = FeedConsumer(group_id="feed-service")
    consumer.start()
"""

from __future__ import annotations

import json
import logging
import signal
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)


class BaseKafkaConsumer:
    """
    Abstract base for Kafka consumers.

    Subclass and implement:
        topics       : list[str]  — topics to subscribe to
        handle_message(topic, event_data) → None
    """

    topics: list[str] = []

    def __init__(self, group_id: str) -> None:
        self.group_id = group_id
        self._running = False
        self._consumer: Any = None

    # ── Abstract method ───────────────────────────────────────────────────────

    def handle_message(self, topic: str, event_data: dict) -> None:
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement handle_message()"
        )

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self) -> None:
        """
        Start the consume loop.  Blocks until stop() is called or
        a SIGTERM / SIGINT is received.
        """
        kafka_enabled = getattr(settings, "KAFKA_ENABLED", False)
        if not kafka_enabled:
            logger.info(
                "%s: KAFKA_ENABLED=False, consumer not started", self.__class__.__name__
            )
            return

        self._setup_consumer()
        self._setup_signal_handlers()
        self._running = True
        logger.info(
            "%s: starting on topics=%s group=%s",
            self.__class__.__name__,
            self.topics,
            self.group_id,
        )
        self._consume_loop()

    def stop(self) -> None:
        self._running = False
        logger.info("%s: stopping", self.__class__.__name__)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _setup_consumer(self) -> None:
        try:
            from confluent_kafka import Consumer  # type: ignore[import]

            bootstrap = getattr(settings, "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
            config = {
                "bootstrap.servers": bootstrap,
                "group.id": self.group_id,
                "auto.offset.reset": "earliest",
                "enable.auto.commit": False,  # manual commit for at-least-once
            }
            self._consumer = Consumer(config)
            self._consumer.subscribe(self.topics)
        except ImportError:
            logger.error("confluent_kafka not installed — cannot start consumer")
            raise

    def _consume_loop(self) -> None:

        try:
            while self._running:
                msg = self._consumer.poll(timeout=1.0)

                if msg is None:
                    continue
                if msg.error():
                    logger.error(
                        "%s: Kafka error: %s", self.__class__.__name__, msg.error()
                    )
                    continue

                try:
                    event_data = json.loads(msg.value().decode("utf-8"))
                    self.handle_message(msg.topic(), event_data)
                    self._consumer.commit(message=msg)  # manual commit on success
                except json.JSONDecodeError:
                    logger.error(
                        "%s: failed to deserialise message on topic=%s",
                        self.__class__.__name__,
                        msg.topic(),
                    )
                except Exception:
                    logger.exception(
                        "%s: unhandled error processing message on topic=%s",
                        self.__class__.__name__,
                        msg.topic(),
                    )
                    # Don't commit — message will be redelivered (at-least-once)

        finally:
            self._consumer.close()
            logger.info("%s: consumer closed", self.__class__.__name__)

    def _setup_signal_handlers(self) -> None:
        signal.signal(signal.SIGTERM, lambda *_: self.stop())
        signal.signal(signal.SIGINT, lambda *_: self.stop())
