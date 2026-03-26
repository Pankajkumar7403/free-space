# 📁 Location: backend/apps/media/services.py

from __future__ import annotations

import logging
from dataclasses import dataclass

from django.db import transaction

from apps.media import tasks as media_tasks
from apps.media.storage import (
    build_cdn_url,
    build_s3_key,
    generate_presigned_upload_url,
)
from apps.posts.constants import MediaStatus
from apps.posts.exceptions import MediaNotFoundError
from apps.posts.models import Media
from apps.posts.validators import validate_file_size, validate_media_mime_type
from apps.users.models import User

logger = logging.getLogger(__name__)


@dataclass
class PresignedUploadResult:
    media_id: str
    upload_url: str
    expires_in: int
    media_type: str


@transaction.atomic
def create_media_record(
    *,
    owner: User,
    mime_type: str,
    file_size: int,
    alt_text: str = "",
) -> PresignedUploadResult:
    """
    Step 1 of the upload flow.
    Validates the file type/size, creates a Media record (status=PENDING),
    and returns a presigned S3 PUT URL for direct client upload.

    The client uploads directly to S3 — the backend never handles the bytes.
    """
    media_type = validate_media_mime_type(mime_type)
    validate_file_size(file_size, mime_type)

    s3_key = build_s3_key("originals", mime_type)
    upload_url = generate_presigned_upload_url(s3_key=s3_key, mime_type=mime_type)

    media = Media.objects.create(
        owner=owner,
        media_type=media_type,
        mime_type=mime_type,
        file_size=file_size,
        alt_text=alt_text,
        original_key=s3_key,
        original_url=build_cdn_url(s3_key),
        status=MediaStatus.PENDING,
    )

    return PresignedUploadResult(
        media_id=str(media.id),
        upload_url=upload_url,
        expires_in=900,
        media_type=media_type,
    )


@transaction.atomic
def confirm_upload(*, media_id, owner: User) -> Media:
    """
    Step 2 of the upload flow.
    Called after the client successfully uploads to S3.
    Updates status to UPLOADED and enqueues the transcoding Celery task.
    """
    try:
        media = Media.objects.get(pk=media_id, owner=owner, is_deleted=False)
    except Media.DoesNotExist:
        raise MediaNotFoundError(detail={"media_id": str(media_id)})

    media.status = MediaStatus.UPLOADED
    media.save(update_fields=["status", "updated_at"])

    # Enqueue async transcoding task
    media_tasks.process_media_task.delay(str(media.id))

    return media


@transaction.atomic
def update_media_status(
    *,
    media_id: str,
    status: str,
    processed_key: str = "",
    thumbnail_key: str = "",
    width: int | None = None,
    height: int | None = None,
    duration: float | None = None,
) -> Media:
    """
    Called by the Celery transcoder task to update processing results.
    Sets CDN URLs from S3 keys.
    """
    try:
        media = Media.objects.get(pk=media_id)
    except Media.DoesNotExist:
        raise MediaNotFoundError(detail={"media_id": media_id})

    updated_fields = ["status", "updated_at"]
    media.status = status

    if processed_key:
        media.processed_key = processed_key
        media.processed_url = build_cdn_url(processed_key)
        updated_fields += ["processed_key", "processed_url"]

    if thumbnail_key:
        media.thumbnail_key = thumbnail_key
        media.thumbnail_url = build_cdn_url(thumbnail_key)
        updated_fields += ["thumbnail_key", "thumbnail_url"]

    for field_name, val in [
        ("width", width),
        ("height", height),
        ("duration", duration),
    ]:
        if val is not None:
            setattr(media, field_name, val)
            updated_fields.append(field_name)

    media.save(update_fields=updated_fields)
    return media
