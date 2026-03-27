# 📁 Location: backend/apps/comments/validators.py

from apps.comments.constants import MAX_COMMENT_LENGTH
from core.exceptions.base import ValidationError


def validate_comment_content(content: str) -> None:
    if not content or not content.strip():
        raise ValidationError("Comment cannot be empty.", code="COMMENT_EMPTY")
    if len(content) > MAX_COMMENT_LENGTH:
        raise ValidationError(
            f"Comment cannot exceed {MAX_COMMENT_LENGTH} characters.",
            code="COMMENT_TOO_LONG",
        )
