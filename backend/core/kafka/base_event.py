"""
core/kafka/base_event.py
~~~~~~~~~~~~~~~~~~~~~~~~
Base dataclass for all Kafka events.

Every event published on the bus inherits from BaseEvent,
ensuring a consistent envelope structure:

    {
        "event_type": "post.created",
        "version":    "1.0",
        "timestamp":  "2025-01-01T00:00:00Z",
        "data":       { ... domain payload ... }
    }

Usage
-----
    from core.kafka.base_event import BaseEvent
    from dataclasses import dataclass

    @dataclass
    class PostCreatedEvent(BaseEvent):
        event_type: str = "post.created"
        post_id:    str = ""
        author_id:  str = ""
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class BaseEvent:
    """
    Root event envelope.

    Fields
    ------
    event_id   : Unique event identifier (UUID4) for deduplication
    event_type : Topic / event name  (e.g. "post.created")
    version    : Schema version — increment when the payload shape changes
    timestamp  : ISO-8601 UTC string of when the event was created
    """

    event_type: str = ""
    version: str = "1.0"
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=_utcnow)

    def to_dict(self) -> dict:
        """Serialise the event to a plain dict for Kafka serialisation."""
        return asdict(self)

    def to_key(self) -> str:
        """
        Return the Kafka message key.

        Default: event_id (random partitioning).
        Override in subclasses to partition by entity:

            def to_key(self) -> str:
                return self.user_id   # all events for a user go to same partition
        """
        return self.event_id