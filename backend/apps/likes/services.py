# 📁 Location: backend/apps/likes/services.py

from __future__ import annotations

import logging

from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from apps.likes.constants import CT_COMMENT, CT_POST
from apps.likes.exceptions import (
    AlreadyLikedError,
    LikeTargetNotFoundError,
    NotLikedError,
)
from apps.likes.models import Like
from apps.users.models import User

logger = logging.getLogger(__name__)


def _resolve_content_type(obj) -> tuple[ContentType, str]:
    """Return (ContentType instance, short label) for a Post or Comment."""
    from apps.comments.models import Comment
    from apps.posts.models import Post

    if isinstance(obj, Post):
        return ContentType.objects.get_for_model(Post), CT_POST
    if isinstance(obj, Comment):
        return ContentType.objects.get_for_model(Comment), CT_COMMENT
    raise LikeTargetNotFoundError(
        message=f"Cannot like object of type {type(obj).__name__}"
    )


@transaction.atomic
def like_object(*, user: User, obj) -> Like:
    """
    Like a Post or Comment.

    Steps
    -----
    1. Check for existing like using unique_together constraint
    2. Create Like DB row

    Raises AlreadyLikedError if user has already liked this object.
    """
    ct, ct_label = _resolve_content_type(obj)
    object_id = str(obj.pk)

    # DB write — unique_together is the final safety net
    try:
        like = Like.objects.create(
            user=user,
            content_type=ct,
            object_id=obj.pk,
        )
    except Exception:
        raise AlreadyLikedError()

    author = getattr(obj, "author", None)
    if author is not None and author.pk != user.pk:
        from apps.notifications.constants import NotificationType
        from apps.notifications.services import create_notification

        content_type_label = "posts.Post" if ct_label == CT_POST else "comments.Comment"
        notification_type = (
            str(NotificationType.LIKE_POST) if ct_label == CT_POST
            else str(NotificationType.LIKE_COMMENT)
        )
        create_notification(
            recipient_id=author.pk,
            actor_id=user.pk,
            notification_type=notification_type,
            target_id=obj.pk,
            target_content_type_label=content_type_label,
        )

    return like


@transaction.atomic
def unlike_object(*, user: User, obj) -> None:
    """
    Unlike a Post or Comment.

    Raises NotLikedError if the user hasn't liked this object.
    """
    ct, ct_label = _resolve_content_type(obj)

    deleted, _ = Like.objects.filter(
        user=user,
        content_type=ct,
        object_id=obj.pk,
    ).delete()

    if not deleted:
        raise NotLikedError()


def get_like_count(*, obj) -> int:
    """
    Return the like count for an object from the database.
    """
    ct = _resolve_content_type(obj)[0]
    return Like.objects.filter(content_type=ct, object_id=obj.pk).count()


def is_liked_by(*, user: User, obj) -> bool:
    """Check whether a specific user has liked an object."""
    ct = _resolve_content_type(obj)[0]
    return Like.objects.filter(user=user, content_type=ct, object_id=obj.pk).exists()
