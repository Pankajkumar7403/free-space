# 📁 Location: backend/apps/posts/events.py

from __future__ import annotations

from dataclasses import dataclass

from core.kafka.base_event import BaseEvent
from core.kafka.producer import get_producer
from core.kafka.topics import Topics


@dataclass
class PostCreatedEvent(BaseEvent):
    event_type: str = Topics.POST_CREATED
    post_id: str = ""
    author_id: str = ""
    visibility: str = ""

    def to_key(self) -> str:
        return self.author_id  # partition by author for ordered delivery


@dataclass
class PostDeletedEvent(BaseEvent):
    event_type: str = Topics.POST_DELETED
    post_id: str = ""
    author_id: str = ""


def emit_post_created(post) -> None:
    """
    Publish post.created event after a successful DB commit.
    Called from create_post() service after transaction.atomic().
    """
    event = PostCreatedEvent(
        post_id=str(post.id),
        author_id=str(post.author_id),
        visibility=post.visibility,
    )
    get_producer().send(Topics.POST_CREATED, event)


def emit_post_deleted(post) -> None:
    event = PostDeletedEvent(
        post_id=str(post.id),
        author_id=str(post.author_id),
    )
    get_producer().send(Topics.POST_DELETED, event)
