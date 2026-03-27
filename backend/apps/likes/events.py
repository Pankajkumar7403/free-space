# 📁 Location: backend/apps/likes/events.py

from __future__ import annotations

from dataclasses import dataclass

from core.kafka.base_event import BaseEvent
from core.kafka.producer import get_producer
from core.kafka.topics import Topics


@dataclass
class LikeCreatedEvent(BaseEvent):
    event_type: str = Topics.LIKE_CREATED
    like_id: str = ""
    user_id: str = ""
    object_id: str = ""
    object_type: str = ""  # "post" or "comment"
    author_id: str = ""  # owner of the liked object (for notification routing)

    def to_key(self) -> str:
        return self.object_id  # partition by object for ordering


def emit_like_created(*, like, ct_label: str, obj) -> None:
    """Emit a like.created Kafka event after a successful like."""
    # Get the author of the liked object for notification routing
    author_id = str(getattr(obj, "author_id", ""))

    event = LikeCreatedEvent(
        like_id=str(like.pk),
        user_id=str(like.user_id),
        object_id=str(like.object_id),
        object_type=ct_label,
        author_id=author_id,
    )
    get_producer().send(Topics.LIKE_CREATED, event)
