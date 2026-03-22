# 📁 Location: backend/apps/comments/services.py

from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction

from apps.comments.constants import MAX_COMMENT_DEPTH
from apps.comments.exceptions import (
    CommentDepthExceededError,
    CommentEditForbiddenError,
    CommentNotFoundError,
    CommentsDisabledError,
)
from apps.comments.models import FLAGGED_KEYWORDS, Comment
from apps.comments.selectors import get_comment_by_id
from apps.comments.validators import validate_comment_content
from apps.posts.selectors import get_post_by_id
from apps.users.models import User

import logging
from apps.comments.events import emit_comment_created
logger = logging.getLogger(__name__)


@dataclass
class CreateCommentInput:
    post_id:   object
    author_id: object
    content:   str
    parent_id: object | None = None


@transaction.atomic
def create_comment(data: CreateCommentInput) -> Comment:
    """
    Create a comment or reply.

    Rules enforced
    --------------
    - Post must have allow_comments=True
    - Reply depth cannot exceed MAX_COMMENT_DEPTH (2)
    - Content is validated for length and emptiness
    - Content is auto-flagged if it contains hate-speech keywords

    Raises
    ------
    CommentsDisabledError, CommentDepthExceededError, ValidationError
    """
    from apps.users.selectors import get_user_by_id

    validate_comment_content(data.content)
    post   = get_post_by_id(data.post_id)
    author = get_user_by_id(data.author_id)

    if not post.allow_comments:
        raise CommentsDisabledError()

    depth  = 0
    parent = None

    if data.parent_id:
        parent = get_comment_by_id(data.parent_id)
        depth  = parent.depth + 1
        if depth > MAX_COMMENT_DEPTH:
            raise CommentDepthExceededError()

    # Auto-flag if content contains hate-speech keywords
    content_lower = data.content.lower()
    is_flagged = any(kw in content_lower for kw in FLAGGED_KEYWORDS)
    if is_flagged:
        logger.warning(
            "create_comment: auto-flagged comment by user=%s", data.author_id
        )

    comment = Comment.objects.create(
        post=post,
        author=author,
        parent=parent,
        content=data.content,
        depth=depth,
        is_flagged=is_flagged,
    )

    # Emit Kafka event for notification system
    emit_comment_created(comment=comment)

    return comment


@transaction.atomic
def update_comment(*, comment_id, requesting_user_id, content: str) -> Comment:
    """
    Edit a comment's content. Only the author can edit.

    Raises CommentNotFoundError, CommentEditForbiddenError
    """
    validate_comment_content(content)
    comment = get_comment_by_id(comment_id)

    if str(comment.author_id) != str(requesting_user_id):
        raise CommentEditForbiddenError()

    comment.content = content
    comment.save(update_fields=["content", "updated_at"])
    comment.refresh_from_db()
    return comment


@transaction.atomic
def delete_comment(*, comment_id, requesting_user_id) -> None:
    """
    Soft-delete a comment. Author OR post owner can delete.

    Raises CommentNotFoundError, CommentEditForbiddenError
    """
    comment = get_comment_by_id(comment_id)

    is_author     = str(comment.author_id) == str(requesting_user_id)
    is_post_owner = str(comment.post.author_id) == str(requesting_user_id)

    if not (is_author or is_post_owner):
        raise CommentEditForbiddenError(
            message="Only the comment author or post owner can delete this comment."
        )

    comment.soft_delete()


@transaction.atomic
def pin_comment(*, comment_id, requesting_user_id) -> Comment:
    """
    Pin a comment to the top of the post's comment section.
    Only the POST OWNER can pin comments.

    Raises CommentEditForbiddenError if requester is not post owner.
    """
    comment = get_comment_by_id(comment_id)

    if str(comment.post.author_id) != str(requesting_user_id):
        raise CommentEditForbiddenError(
            message="Only the post owner can pin comments."
        )

    # Unpin any previously pinned comment on this post
    Comment.objects.filter(post=comment.post, is_pinned=True).update(is_pinned=False)

    comment.is_pinned = True
    comment.save(update_fields=["is_pinned", "updated_at"])
    return comment


@transaction.atomic
def hide_comment(*, comment_id, requesting_user_id) -> Comment:
    """
    Hide a comment. Author OR post owner can hide.
    Hidden comments remain in DB but render as [comment hidden].
    """
    comment = get_comment_by_id(comment_id)

    is_author     = str(comment.author_id) == str(requesting_user_id)
    is_post_owner = str(comment.post.author_id) == str(requesting_user_id)

    if not (is_author or is_post_owner):
        raise CommentEditForbiddenError(
            message="Only the comment author or post owner can hide this comment."
        )

    comment.is_hidden = True
    comment.save(update_fields=["is_hidden", "updated_at"])
    return comment


@transaction.atomic
def report_comment(
    *,
    comment_id,
    reporter_id,
    reason: str = "other",
) -> None:
    """
    Report a comment for moderation review.
    Auto-flags the comment for admin attention.
    """
    comment = get_comment_by_id(comment_id)
    comment.is_flagged = True
    comment.save(update_fields=["is_flagged", "updated_at"])
    logger.info(
        "report_comment: comment=%s reported by user=%s reason=%s",
        comment_id, reporter_id, reason,
    )