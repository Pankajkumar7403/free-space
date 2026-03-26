# 📁 Location: backend/apps/media/tasks.py

from __future__ import annotations

import logging

from celery import shared_task

from apps.posts.constants import MediaStatus

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="media.process_media",
)
def process_media_task(self, media_id: str) -> None:
    """
    Celery task: transcode an uploaded media file.

    Steps
    -----
    1. Fetch media record from DB (status must be UPLOADED)
    2. Download original from S3
    3. Run FFmpeg transcoder (image resize or video compress)
    4. Upload processed file + thumbnail to S3
    5. Update media record with processed URLs (status=READY)
    6. On any failure: mark status=FAILED and retry (max 3x)
    """
    from apps.media.services import update_media_status
    from apps.media.transcoder import transcode_media
    from apps.posts.models import Media

    try:
        media = Media.objects.get(pk=media_id)
    except Media.DoesNotExist:
        logger.error("process_media_task: Media %s not found", media_id)
        return

    if media.status not in (MediaStatus.UPLOADED, MediaStatus.FAILED):
        logger.warning(
            "process_media_task: Media %s in unexpected status %s, skipping",
            media_id,
            media.status,
        )
        return

    # Mark as processing
    update_media_status(media_id=media_id, status=MediaStatus.PROCESSING)

    try:
        result = transcode_media(media)
        update_media_status(
            media_id=media_id,
            status=MediaStatus.READY,
            processed_key=result.processed_key,
            thumbnail_key=result.thumbnail_key,
            width=result.width,
            height=result.height,
            duration=result.duration,
        )
        logger.info("process_media_task: Media %s ready", media_id)

    except Exception as exc:
        logger.exception("process_media_task: failed for media %s", media_id)
        update_media_status(media_id=media_id, status=MediaStatus.FAILED)
        raise self.retry(exc=exc)
