# 📁 Location: backend/apps/likes/services.py

from __future__ import annotations

import logging

from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from apps.likes.cache import has_user_liked, like_decr, like_incr
from apps.likes.constants import CT_COMMENT, CT_POST
from apps.likes.events import emit_like_created
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
    1. Check Redis membership — fast O(1) duplicate check
    2. Create Like DB row (unique_together prevents DB-level duplicates)
    3. Increment Redis counter atomically
    4. Emit Kafka event for notification system

    Raises AlreadyLikedError if user has already liked this object.
    """
    ct, ct_label = _resolve_content_type(obj)
    object_id = str(obj.pk)

    # Fast path: check Redis first (avoids DB query on duplicate)
    if has_user_liked(str(user.pk), ct_label, object_id):
        raise AlreadyLikedError()

    # DB write — unique_together is the final safety net
    try:
        like = Like.objects.create(
            user=user,
            content_type=ct,
            object_id=obj.pk,
        )
    except Exception:
        raise AlreadyLikedError()

    # Increment Redis counter
    like_incr(ct_label, object_id, str(user.pk))

    # Emit Kafka event
    emit_like_created(like=like, ct_label=ct_label, obj=obj)

    return like


@transaction.atomic
def unlike_object(*, user: User, obj) -> None:
    """
    Unlike a Post or Comment.

    Raises NotLikedError if the user hasn't liked this object.
    """
    ct, ct_label = _resolve_content_type(obj)
    object_id = str(obj.pk)

    deleted, _ = Like.objects.filter(
        user=user,
        content_type=ct,
        object_id=obj.pk,
    ).delete()

    if not deleted:
        raise NotLikedError()

    # Decrement Redis counter
    like_decr(ct_label, object_id, str(user.pk))


def get_like_count(*, obj) -> int:
    """
    Return the like count for an object.
    Redis is the source of truth; falls back to DB count on cache miss.
    """
    from apps.likes.cache import get_like_count as redis_count

    ct, ct_label = _resolve_content_type(obj)
    object_id = str(obj.pk)

    cached = redis_count(ct_label, object_id)
    if cached is not None:
        return cached

    # Cache miss — count from DB and warm Redis
    db_count = Like.objects.filter(content_type=ct, object_id=obj.pk).count()
    from apps.likes.cache import set_like_count

    set_like_count(ct_label, object_id, db_count)
    return db_count


def is_liked_by(*, user: User, obj) -> bool:
    """Check whether a specific user has liked an object."""
    ct, ct_label = _resolve_content_type(obj)
    return has_user_liked(str(user.pk), ct_label, str(obj.pk))
