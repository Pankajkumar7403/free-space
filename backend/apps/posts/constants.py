# 📁 Location: backend/apps/posts/constants.py

from django.db import models


class PostVisibility(models.TextChoices):
    PUBLIC = "public", "Public — anyone can see"
    FOLLOWERS_ONLY = "followers_only", "Followers only"
    CLOSE_FRIENDS = "close_friends", "Close friends"
    PRIVATE = "private", "Only me"


class MediaType(models.TextChoices):
    IMAGE = "image", "Image"
    VIDEO = "video", "Video"


class MediaStatus(models.TextChoices):
    PENDING = "pending", "Pending upload"
    UPLOADED = "uploaded", "Uploaded to S3"
    PROCESSING = "processing", "Transcoding in progress"
    READY = "ready", "Ready to serve"
    FAILED = "failed", "Processing failed"


class PostStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"
    ARCHIVED = "archived", "Archived"
