# 📁 Location: backend/apps/comments/events.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from core.kafka.base_event import BaseEvent
from core.kafka.producer import get_producer
from core.kafka.topics import Topics


@dataclass
class CommentCreatedEvent(BaseEvent):
    event_type: str = Topics.COMMENT_CREATED
    comment_id: str = ""
    post_id: str = ""
    author_id: str = ""
    post_author_id: str = ""  # for notification routing
    parent_comment_id: Optional[str] = ""
    parent_comment_author_id: Optional[str] = ""

    def to_key(self) -> str:
        return self.post_id  # partition by post


def emit_comment_created(*, comment) -> None:
    has_parent = comment.parent_id is not None
    event = CommentCreatedEvent(
        comment_id=str(comment.pk),
        post_id=str(comment.post_id),
        author_id=str(comment.author_id),
        post_author_id=str(comment.post.author_id),
        parent_comment_id=str(comment.parent_id) if has_parent else "",
        parent_comment_author_id=str(comment.parent.author_id) if has_parent else "",
    )
    get_producer().send(Topics.COMMENT_CREATED, event)
