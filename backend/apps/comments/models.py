# 📁 Location: backend/apps/comments/models.py

from __future__ import annotations

from django.db import models

from apps.users.models import User
from core.database.base_model import BaseModel


class Comment(BaseModel):
    """
    A comment on a post, with optional threading (up to 3 levels deep).

    Threading structure
    -------------------
    Level 0  top-level comment   (parent=None)
    Level 1  reply to a comment  (parent=level-0 comment)
    Level 2  reply to a reply    (parent=level-1 comment)
    Level 3+ NOT ALLOWED         (enforced in service layer)

    Why limit to 3 levels?
    - Deep nesting is hard to render on mobile
    - Keeps pagination simple (load top-level, lazy-load replies)
    - Instagram/Twitter use 2 levels; we allow one extra for nuance

    Moderation fields
    -----------------
    is_hidden     → hidden by author or post owner (still in DB, shows as [hidden])
    is_pinned     → pinned to top of comment section by post author
    is_flagged    → auto-flagged by keyword filter, pending moderation review
    """

    post = models.ForeignKey(
        "posts.Post",
        on_delete=models.CASCADE,
        related_name="comments",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="replies",
        help_text="Null for top-level comments; set for replies.",
    )
    content = models.TextField(max_length=1000)
    depth = models.PositiveSmallIntegerField(
        default=0,
        help_text="0 = top-level, 1 = reply, 2 = reply-to-reply. Max 2.",
    )
    is_hidden = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)
    is_flagged = models.BooleanField(default=False)

    class Meta:
        db_table = "comments_comment"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["post", "parent", "is_deleted"]),
            models.Index(fields=["post", "is_pinned", "created_at"]),
        ]

    def __str__(self) -> str:
        preview = self.content[:50] + "…" if len(self.content) > 50 else self.content
        return f"Comment({self.author_id}): {preview}"

    @property
    def is_reply(self) -> bool:
        return self.parent_id is not None

    @property
    def reply_count(self) -> int:
        """Live DB count of non-deleted replies."""
        return self.replies.filter(is_deleted=False).count()


# Auto-flagging keyword list (expanded in M7 with ML classifier)
FLAGGED_KEYWORDS = [
    "faggot",
    "tranny",
    "dyke",
    "homo",
    "queer",  # context-dependent — flagged for human review, not auto-removed
]
