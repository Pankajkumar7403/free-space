# 📁 Location: backend/apps/posts/models.py

from __future__ import annotations

import uuid

from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db import models

from apps.posts.constants import MediaStatus, MediaType, PostStatus, PostVisibility
from apps.users.models import User
from core.database.base_model import BaseModel


class Hashtag(models.Model):
    """
    Normalised hashtag — one row per unique tag string.
    Posts reference hashtags via M2M through PostHashtag.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "posts_hashtag"
        ordering = ["name"]

    def __str__(self) -> str:
        return f"#{self.name}"


class Media(BaseModel):
    """
    A single uploaded file (image or video).
    One Post can have multiple Media items (up to 10).

    Upload flow
    -----------
    1. Client requests presigned URL   → POST /api/v1/media/presign/
    2. Client uploads directly to S3   → PUT <presigned_url>
    3. Client notifies upload complete → POST /api/v1/media/<id>/confirm/
    4. Celery task transcodes          → status goes PROCESSING → READY
    """

    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="media_files"
    )
    media_type = models.CharField(max_length=10, choices=MediaType.choices)
    status = models.CharField(
        max_length=12, choices=MediaStatus.choices, default=MediaStatus.PENDING
    )

    # S3 keys — stored without the bucket prefix for portability
    original_key = models.CharField(max_length=512, blank=True)
    processed_key = models.CharField(max_length=512, blank=True)
    thumbnail_key = models.CharField(max_length=512, blank=True)

    # CDN-served public URLs (set after transcoding is complete)
    original_url = models.URLField(max_length=1024, blank=True)
    processed_url = models.URLField(max_length=1024, blank=True)
    thumbnail_url = models.URLField(max_length=1024, blank=True)

    # Metadata
    file_size = models.PositiveBigIntegerField(default=0, help_text="Bytes")
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    duration = models.FloatField(
        null=True, blank=True, help_text="Video duration in seconds"
    )
    mime_type = models.CharField(max_length=100, blank=True)
    alt_text = models.CharField(
        max_length=500, blank=True, help_text="Accessibility alt text"
    )

    class Meta:
        db_table = "posts_media"
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"{self.media_type}:{self.id} ({self.status})"

    @property
    def is_ready(self) -> bool:
        return self.status == MediaStatus.READY

    @property
    def display_url(self) -> str:
        """Return the best available URL for serving to clients."""
        return self.processed_url or self.original_url or ""


class Post(BaseModel):
    """
    Core post model.

    Key design decisions
    --------------------
    - search_vector: PostgreSQL tsvector kept in sync via DB trigger (set up in migration)
    - is_anonymous: LGBTQ+ safety feature — author identity hidden from feed
    - media: M2M through PostMedia with ordering (position field)
    - hashtags: M2M through PostHashtag (upserted on save)
    """

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    content = models.TextField(max_length=2200, blank=True)
    status = models.CharField(
        max_length=12, choices=PostStatus.choices, default=PostStatus.PUBLISHED
    )
    visibility = models.CharField(
        max_length=15,
        choices=PostVisibility.choices,
        default=PostVisibility.FOLLOWERS_ONLY,
    )
    allow_comments = models.BooleanField(default=True)
    is_anonymous = models.BooleanField(
        default=False, help_text="LGBTQ+ safety: hides author identity"
    )

    # Location (opt-in only)
    location_name = models.CharField(max_length=200, blank=True)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )

    # Relations
    hashtags = models.ManyToManyField(Hashtag, through="PostHashtag", blank=True)
    media = models.ManyToManyField(Media, through="PostMedia", blank=True)

    # Full-text search vector (auto-updated by DB trigger in migration)
    search_vector = SearchVectorField(null=True, blank=True)

    class Meta:
        db_table = "posts_post"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["author", "status", "created_at"]),
            models.Index(fields=["visibility", "status"]),
            models.Index(fields=["is_deleted", "status", "created_at"]),
            GinIndex(fields=["search_vector"], name="posts_search_gin"),
        ]

    def __str__(self) -> str:
        preview = self.content[:60] + "…" if len(self.content) > 60 else self.content
        return f"Post({self.id}): {preview}"


class PostHashtag(models.Model):
    """Through table for Post ↔ Hashtag M2M."""

    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    hashtag = models.ForeignKey(Hashtag, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "posts_post_hashtag"
        unique_together = [("post", "hashtag")]


class PostMedia(models.Model):
    """Through table for Post ↔ Media M2M with ordering."""

    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    media = models.ForeignKey(Media, on_delete=models.CASCADE)
    position = models.PositiveSmallIntegerField(
        default=0, help_text="Display order within post"
    )

    class Meta:
        db_table = "posts_post_media"
        unique_together = [("post", "media")]
        ordering = ["position"]
