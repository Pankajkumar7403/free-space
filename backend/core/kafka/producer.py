"""
core/kafka/producer.py
~~~~~~~~~~~~~~~~~~~~~~
KafkaProducer wrapper around confluent-kafka-python.

Design decisions
----------------
- Singleton producer per process (expensive to create, thread-safe to use).
- JSON serialisation by default (swap to Avro/Protobuf later without changing callers).
- Fire-and-forget with on_delivery callback for error logging.
- In test/dev environments, the producer is a no-op mock so tests run offline.

Usage
-----
    from core.kafka.producer import get_producer
    from core.kafka.topics import Topics

    producer = get_producer()
    producer.send(Topics.POST_CREATED, event)   # event is a BaseEvent instance
"""

from __future__ import annotations

import json
import logging
from typing import Any

from django.conf import settings

from core.kafka.base_event import BaseEvent

logger = logging.getLogger(__name__)

_producer_instance: Any = None


class MockKafkaProducer:
    """
    No-op producer used in tests and when Kafka is disabled.

    Records all sent messages so tests can assert on them:
        producer = get_producer()
        assert producer.sent[0]["topic"] == "post.created"
    """

    def __init__(self) -> None:
        self.sent: list[dict] = []

    def send(self, topic: str, event: BaseEvent, key: str | None = None) -> None:
        entry = {"topic": topic, "event": event.to_dict(), "key": key or event.to_key()}
        self.sent.append(entry)
        logger.debug("MockKafkaProducer: queued %s on %s", event.event_type, topic)

    def flush(self, timeout: float = 10.0) -> None:
        pass  # Nothing to flush

    def reset(self) -> None:
        """Clear sent messages between tests."""
        self.sent.clear()


class KafkaProducer:
    """
    Production Kafka producer.

    Wraps confluent_kafka.Producer with:
      - JSON serialisation
      - delivery report logging
      - automatic flush on graceful shutdown
    """

    def __init__(self, config: dict) -> None:
        from confluent_kafka import Producer  # type: ignore[import]

        self._producer = Producer(config)
        logger.info("KafkaProducer: connected to %s", config.get("bootstrap.servers"))

    def send(self, topic: str, event: BaseEvent, key: str | None = None) -> None:
        """
        Publish *event* to *topic*.

        Parameters
        ----------
        topic   : Kafka topic string (use Topics.* constants)
        event   : Domain event dataclass (BaseEvent subclass)
        key     : Optional partition key (defaults to event.to_key())
        """
        message_key = (key or event.to_key()).encode("utf-8")
        value = json.dumps(event.to_dict()).encode("utf-8")

        self._producer.produce(
            topic=topic,
            key=message_key,
            value=value,
            on_delivery=self._on_delivery,
        )
        # poll() triggers delivery callbacks without blocking
        self._producer.poll(0)

    def flush(self, timeout: float = 10.0) -> None:
        """Block until all queued messages are delivered or *timeout* expires."""
        self._producer.flush(timeout)

    @staticmethod
    def _on_delivery(err: Any, msg: Any) -> None:
        if err:
            logger.error(
                "KafkaProducer delivery failed: topic=%s partition=%s error=%s",
                msg.topic(),
                msg.partition(),
                err,
            )
        else:
            logger.debug(
                "KafkaProducer delivered: topic=%s partition=%s offset=%s",
                msg.topic(),
                msg.partition(),
                msg.offset(),
            )


# ── Singleton factory ─────────────────────────────────────────────────────────


def get_producer() -> KafkaProducer | MockKafkaProducer:
    """
    Return the module-level producer singleton.

    Returns MockKafkaProducer when:
      - KAFKA_ENABLED = False in settings (default in dev/test)
      - confluent_kafka is not installed
    """
    global _producer_instance  # noqa: PLW0603

    if _producer_instance is not None:
        return _producer_instance

    kafka_enabled = getattr(settings, "KAFKA_ENABLED", False)

    if not kafka_enabled:
        _producer_instance = MockKafkaProducer()
        logger.info("KafkaProducer: using MockKafkaProducer (KAFKA_ENABLED=False)")
        return _producer_instance

    try:
        bootstrap_servers = getattr(
            settings, "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"
        )
        config = {
            "bootstrap.servers": bootstrap_servers,
            "acks": "all",  # wait for all replicas
            "retries": 3,
            "linger.ms": 5,  # micro-batching
            "compression.type": "snappy",
        }
        _producer_instance = KafkaProducer(config)
    except ImportError:
        logger.warning("confluent_kafka not installed — using MockKafkaProducer")
        _producer_instance = MockKafkaProducer()

    return _producer_instance


def reset_producer() -> None:
    """Force singleton recreation — use in tests."""
    global _producer_instance  # noqa: PLW0603
    _producer_instance = None
