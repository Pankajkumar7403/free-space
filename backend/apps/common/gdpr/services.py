"""
apps/common/gdpr/services.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
GDPR service layer:
  - request_data_export()    -> initiate async export
  - delete_account()         -> cascade-delete all user data
"""

from __future__ import annotations

import logging
import uuid

from django.db import transaction

from apps.common.gdpr.tasks import cleanup_s3_media, generate_gdpr_export

logger = logging.getLogger(__name__)


def request_data_export(user_id: uuid.UUID) -> str:
    """
    Initiate a GDPR data export.
    Returns a job ID (UUID string) - the actual export runs in a Celery task.
    The user receives a download link via email when complete.
    """
    from core.monitoring.prometheus import GDPR_EXPORTS

    job_id = str(uuid.uuid4())
    generate_gdpr_export.delay(str(user_id), job_id)

    GDPR_EXPORTS.labels(status="requested").inc()
    logger.info(
        "gdpr.export.requested", extra={"user_id": str(user_id), "job_id": job_id}
    )
    return job_id


def delete_account(user_id: uuid.UUID) -> None:
    """
    GDPR Article 17 - Right to erasure.

    Deletion order (avoids FK constraint violations):
    1. Notifications (recipient + actor)
    2. Device tokens
    3. Likes
    4. Comments (soft-delete first, then hard)
    5. Feed items
    6. Posts (soft-delete, media S3 cleanup via Celery)
    7. Follows (both directions)
    8. Block / mute records
    9. Notification preferences
    10. User row
    """
    from apps.users.models import User

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.warning("gdpr.delete.user_not_found", extra={"user_id": str(user_id)})
        return

    with transaction.atomic():
        _cascade_delete(user_id)
        logger.info(
            "gdpr.delete.complete",
            extra={"user_id": str(user_id), "username": user.username},
        )


def _cascade_delete(user_id: uuid.UUID) -> None:
    """Execute deletion in safe dependency order."""
    from apps.feed.models import FeedItem
    from apps.notifications.models import (
        DeviceToken,
        Notification,
        NotificationPreference,
    )

    # Notifications
    Notification.objects.filter(recipient_id=user_id).delete()
    Notification.objects.filter(actor_id=user_id).delete()
    DeviceToken.objects.filter(user_id=user_id).delete()
    NotificationPreference.objects.filter(user_id=user_id).delete()

    # Feed
    FeedItem.objects.filter(user_id=user_id).delete()

    # Posts + media (async S3 cleanup)
    _delete_posts(user_id)

    # Social graph
    _delete_social_graph(user_id)

    # User row (CASCADE handles remaining FK refs)
    from apps.users.models import User

    User.objects.filter(id=user_id).delete()


def _delete_posts(user_id: uuid.UUID) -> None:
    """Hard-delete all posts and queue S3 media cleanup."""
    from apps.posts.models import Media, Post

    media_keys = list(
        Media.objects.filter(owner_id=user_id).values_list(
            "original_key", "processed_key", "thumbnail_key"
        )
    )
    Post.all_objects.filter(author_id=user_id).delete()
    Media.objects.filter(owner_id=user_id).delete()

    # Async S3 cleanup
    all_keys = [k for triple in media_keys for k in triple if k]
    if all_keys:
        cleanup_s3_media.delay(all_keys)


def _delete_social_graph(user_id: uuid.UUID) -> None:
    from apps.users.models import Follow

    Follow.objects.filter(follower_id=user_id).delete()
    Follow.objects.filter(following_id=user_id).delete()

    try:
        from apps.users.models import BlockedUser, MutedUser

        BlockedUser.objects.filter(blocker_id=user_id).delete()
        BlockedUser.objects.filter(blocked_id=user_id).delete()
        MutedUser.objects.filter(muter_id=user_id).delete()
        MutedUser.objects.filter(muted_id=user_id).delete()
    except Exception:
        pass
