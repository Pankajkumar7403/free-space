# 📁 Location: backend/apps/posts/validators.py

from __future__ import annotations

from apps.posts.constants import MediaType
from apps.posts.exceptions import (
    FileTooLargeError,
    InvalidMediaTypeError,
    MediaLimitExceededError,
)
from core.exceptions.base import ValidationError

# ── Limits ────────────────────────────────────────────────────────────────────
MAX_POST_LENGTH = 2200
MAX_MEDIA_PER_POST = 10
MAX_IMAGE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB
MAX_VIDEO_SIZE_BYTES = 500 * 1024 * 1024  # 500 MB

ALLOWED_IMAGE_MIME = {"image/jpeg", "image/png", "image/gif", "image/webp"}
ALLOWED_VIDEO_MIME = {"video/mp4", "video/quicktime", "video/x-msvideo"}
ALLOWED_MIME_TYPES = ALLOWED_IMAGE_MIME | ALLOWED_VIDEO_MIME


def validate_post_content(content: str) -> None:
    if not content or not content.strip():
        raise ValidationError(
            "Post content cannot be empty.", code="POST_CONTENT_EMPTY"
        )
    if len(content) > MAX_POST_LENGTH:
        raise ValidationError(
            f"Post content cannot exceed {MAX_POST_LENGTH} characters.",
            code="POST_CONTENT_TOO_LONG",
        )


def validate_media_count(current_count: int) -> None:
    if current_count >= MAX_MEDIA_PER_POST:
        raise MediaLimitExceededError(
            detail={"limit": MAX_MEDIA_PER_POST, "current": current_count}
        )


def validate_media_mime_type(mime_type: str) -> str:
    """
    Validate MIME type and return the MediaType enum value.
    Raises InvalidMediaTypeError on unsupported types.
    """
    mime_type = mime_type.lower().strip()
    if mime_type not in ALLOWED_MIME_TYPES:
        raise InvalidMediaTypeError(detail={"mime_type": mime_type})
    return (
        str(MediaType.IMAGE)
        if mime_type in ALLOWED_IMAGE_MIME
        else str(MediaType.VIDEO)
    )


def validate_file_size(size_bytes: int, mime_type: str) -> None:
    """Validate uploaded file size against per-type limits."""
    if mime_type in ALLOWED_IMAGE_MIME:
        limit = MAX_IMAGE_SIZE_BYTES
        label = "20 MB"
    else:
        limit = MAX_VIDEO_SIZE_BYTES
        label = "500 MB"

    if size_bytes > limit:
        raise FileTooLargeError(
            detail={"max_bytes": limit, "max_label": label, "actual_bytes": size_bytes}
        )
