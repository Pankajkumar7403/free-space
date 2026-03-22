# 📁 Location: backend/apps/comments/selectors.py

from __future__ import annotations

from django.db.models import QuerySet

from apps.comments.exceptions import CommentNotFoundError
from apps.comments.models import Comment
from apps.users.models import User


def get_comment_by_id(comment_id) -> Comment:
    """Raises CommentNotFoundError if not found or soft-deleted."""
    try:
        return Comment.objects.select_related(
            "author", "post", "parent"
        ).get(pk=comment_id, is_deleted=False)
    except Comment.DoesNotExist:
        raise CommentNotFoundError(detail={"comment_id": str(comment_id)})


def get_top_level_comments(*, post_id) -> QuerySet:
    """
    Return top-level (depth=0) comments for a post.
    Pinned comments first, then chronological.
    Hidden comments included but marked — client decides how to render.
    """
    return (
        Comment.objects
        .filter(post_id=post_id, parent=None, is_deleted=False)
        .select_related("author")
        .order_by("-is_pinned", "created_at")
    )


def get_replies(*, parent_id) -> QuerySet:
    """Return all non-deleted replies to a comment, oldest first."""
    return (
        Comment.objects
        .filter(parent_id=parent_id, is_deleted=False)
        .select_related("author")
        .order_by("created_at")
    )


def get_comment_count(*, post_id) -> int:
    """Total non-deleted, non-hidden comment count for a post."""
    return Comment.objects.filter(
        post_id=post_id, is_deleted=False, is_hidden=False
    ).count()