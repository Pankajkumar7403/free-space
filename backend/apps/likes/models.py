# 📁 Location: backend/apps/likes/models.py

from __future__ import annotations

import uuid

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from apps.users.models import User


class Like(models.Model):
    """
    A like on any likeable object — currently Post or Comment.

    Uses Django's GenericForeignKey so one model handles both,
    rather than having separate PostLike and CommentLike tables.

    Design decisions
    ----------------
    - content_type + object_id  →  GenericForeignKey pattern
    - unique_together on (user, content_type, object_id) prevents duplicate likes
    - like COUNT is stored in Redis (fast), reconciled to DB every 5 min via Celery
    - DB like_count column is the fallback when Redis is cold

    Redis key schema
    ----------------
    likes:{content_type}:{object_id}   →  integer counter
    liked:{user_id}:{content_type}:{object_id}  →  "1" (membership check)
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="likes")
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField(db_index=True)
    content_object = GenericForeignKey("content_type", "object_id")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "likes_like"
        unique_together = [("user", "content_type", "object_id")]
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]

    def __str__(self) -> str:
        return f"Like(user={self.user_id}, object={self.object_id})"
