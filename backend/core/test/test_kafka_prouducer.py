# 📁 Location: backend/core/tests/test_kafka_producer.py
# ▶  Run:      pytest core/tests/test_kafka_producer.py -v
"""
test_kafka_producer.py
~~~~~~~~~~~~~~~~~~~~~~
Tests for core/kafka/producer.py

Uses MockKafkaProducer — no real Kafka broker needed.
"""

from __future__ import annotations

import pytest

from core.kafka.base_event import BaseEvent
from core.kafka.producer import MockKafkaProducer, get_producer, reset_producer
from core.kafka.topics import Topics

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def reset():
    reset_producer()
    yield
    reset_producer()


class TestMockKafkaProducer:
    def test_get_producer_returns_mock_when_kafka_disabled(self):
        producer = get_producer()
        assert isinstance(producer, MockKafkaProducer)

    def test_send_records_message(self):
        from dataclasses import dataclass

        @dataclass
        class PostCreated(BaseEvent):
            event_type: str = Topics.POST_CREATED
            post_id: str = ""

        producer = get_producer()
        event = PostCreated(post_id="post-123")
        producer.send(Topics.POST_CREATED, event)

        assert len(producer.sent) == 1
        assert producer.sent[0]["topic"] == Topics.POST_CREATED
        assert producer.sent[0]["event"]["post_id"] == "post-123"

    def test_reset_clears_sent_messages(self):
        from dataclasses import dataclass

        @dataclass
        class DummyEvent(BaseEvent):
            event_type: str = "test.event"

        producer = get_producer()
        producer.send("test.event", DummyEvent())
        assert len(producer.sent) == 1

        producer.reset()
        assert len(producer.sent) == 0

    def test_flush_does_not_raise(self):
        producer = get_producer()
        producer.flush()  # should be a no-op


class TestBaseEvent:
    def test_event_has_unique_id(self):
        e1 = BaseEvent(event_type="test")
        e2 = BaseEvent(event_type="test")
        assert e1.event_id != e2.event_id

    def test_event_has_timestamp(self):
        e = BaseEvent(event_type="test")
        assert e.timestamp is not None
        assert "T" in e.timestamp  # ISO 8601

    def test_to_dict_returns_serialisable_dict(self):
        e = BaseEvent(event_type="test.created", version="1.0")
        d = e.to_dict()
        assert d["event_type"] == "test.created"
        assert d["version"] == "1.0"
        assert "event_id" in d
        assert "timestamp" in d


class TestTopics:
    def test_all_returns_list_of_strings(self):
        all_topics = Topics.all()
        assert isinstance(all_topics, list)
        assert all(isinstance(t, str) for t in all_topics)

    def test_known_topics_are_present(self):
        all_topics = Topics.all()
        assert Topics.POST_CREATED in all_topics
        assert Topics.USER_FOLLOWED in all_topics
        assert Topics.LIKE_CREATED in all_topics
