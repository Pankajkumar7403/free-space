"""
core/kafka/topics.py
~~~~~~~~~~~~~~~~~~~~
Single source of truth for all Kafka topic names.

Import from here everywhere — never hardcode topic strings.

Convention
----------
  <domain>.<event_verb>   e.g.  post.created, user.followed
"""

from __future__ import annotations


class Topics:
    # ── Posts ─────────────────────────────────────────────────────────────────
    POST_CREATED = "post.created"
    POST_UPDATED = "post.updated"
    POST_DELETED = "post.deleted"

    # ── Users ─────────────────────────────────────────────────────────────────
    USER_REGISTERED = "user.registered"
    USER_FOLLOWED = "user.followed"
    USER_UNFOLLOWED = "user.unfollowed"
    USER_BLOCKED = "user.blocked"

    # ── Likes ─────────────────────────────────────────────────────────────────
    LIKE_CREATED = "like.created"
    LIKE_REMOVED = "like.removed"

    # ── Comments ──────────────────────────────────────────────────────────────
    COMMENT_CREATED = "comment.created"
    COMMENT_DELETED = "comment.deleted"

    # ── Notifications ─────────────────────────────────────────────────────────
    NOTIFICATION_DISPATCH = "notification.dispatch"

    # ── Media ─────────────────────────────────────────────────────────────────
    MEDIA_UPLOAD_COMPLETE = "media.upload_complete"
    MEDIA_TRANSCODE_COMPLETE = "media.transcode_complete"

    @classmethod
    def all(cls) -> list[str]:
        """Return all registered topic name strings."""
        return [
            v
            for k, v in vars(cls).items()
            if not k.startswith("_") and isinstance(v, str)
        ]
