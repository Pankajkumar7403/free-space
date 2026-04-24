from __future__ import annotations

from dataclasses import dataclass

from core.kafka.base_event import BaseEvent
from core.kafka.producer import get_producer
from core.kafka.topics import Topics


@dataclass
class UserFollowedEvent(BaseEvent):
    event_type: str = Topics.USER_FOLLOWED
    follower_id: str = ""
    following_id: str = ""

    def to_key(self) -> str:
        return self.following_id


def emit_user_followed(*, follower_id: str, following_id: str) -> None:
    event = UserFollowedEvent(
        follower_id=follower_id,
        following_id=following_id,
    )
    get_producer().send(Topics.USER_FOLLOWED, event)
