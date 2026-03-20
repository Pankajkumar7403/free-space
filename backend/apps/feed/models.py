# 📁 Location: backend/apps/feed/models.py

from __future__ import annotations

import uuid

from django.db import models

from apps.feed.constants import FeedSource
from apps.users.models import User


class FeedItem(models.Model):
    """
    A single entry in a user's feed.

    This DB table is the FALLBACK for when Redis is unavailable or cold.
    The primary feed store is Redis ZSets — this table provides durability.

    Design decisions
    ----------------
    - No soft-delete: feed items are ephemeral — we hard-delete them
      when a post is deleted or a user unfollows someone.
    - score: pre-computed ranking score stored so re-ranking a cold feed
      doesn't require fetching all posts again.
    - source: tells the client WHY this post is in their feed
      (followed user, hashtag subscription, or explore recommendation).
    """

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user       = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="feed_items",
        help_text="The user whose feed this item belongs to.",
    )
    post_id    = models.UUIDField(db_index=True)
    score      = models.FloatField(
        default=0.0,
        help_text="Pre-computed ranking score. Higher = shown earlier.",
    )
    source     = models.CharField(
        max_length=10, choices=FeedSource.choices, default=FeedSource.FOLLOW,
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table        = "feed_item"
        unique_together = [("user", "post_id")]
        indexes         = [
            models.Index(fields=["user", "score"]),
            models.Index(fields=["user", "created_at"]),
        ]
        ordering = ["-score", "-created_at"]

    def __str__(self) -> str:
        return f"FeedItem(user={self.user_id}, post={self.post_id})"


class HashtagSubscription(models.Model):
    """
    A user subscribes to a hashtag — their feed includes posts with that tag.
    """

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name="hashtag_subscriptions")
    hashtag    = models.ForeignKey(
        "posts.Hashtag", on_delete=models.CASCADE, related_name="subscribers",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = "feed_hashtag_subscription"
        unique_together = [("user", "hashtag")]

    def __str__(self) -> str:
        return f"{self.user.username} → #{self.hashtag.name}"