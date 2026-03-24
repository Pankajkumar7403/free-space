from __future__ import annotations

import logging
import uuid

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def classify_media_image(self, media_id: str) -> None:
    """
    Async NSFW image classification.
    Called after media reaches READY status.
    Quarantines media if BLOCK confidence exceeded.
    """
    from apps.media.models import Media
    from apps.media.constants import MediaStatus
    from apps.common.moderation.image_classifier import classify_image, ModerationAction

    try:
        media = Media.objects.get(id=uuid.UUID(media_id))
    except Media.DoesNotExist:
        return

    if not media.processed_key:
        return

    result = classify_image(media.processed_key)

    if result.action == ModerationAction.BLOCK:
        media.status = MediaStatus.FAILED
        media.error_message = (
            f"[MODERATION] Image blocked: {result.label} ({result.confidence:.0%})"
        )
        media.save(update_fields=["status", "error_message"])
        logger.warning(
            "moderation.image.blocked",
            extra={
                "media_id": media_id,
                "label": result.label,
                "confidence": result.confidence,
            },
        )
    elif result.action == ModerationAction.WARN:
        logger.info(
            "moderation.image.flagged",
            extra={"media_id": media_id, "label": result.label},
        )
