# 📁 Location: backend/apps/media/storage.py

from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING

from django.conf import settings

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# ── S3 key schema ─────────────────────────────────────────────────────────────
# originals/{year}/{month}/{uuid}.{ext}
# processed/{year}/{month}/{uuid}.{ext}
# thumbnails/{year}/{month}/{uuid}.jpg

_ALLOWED_EXTENSIONS = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/gif": "gif",
    "image/webp": "webp",
    "video/mp4": "mp4",
    "video/quicktime": "mov",
}


def build_s3_key(prefix: str, mime_type: str) -> str:
    """
    Build a deterministic, unique S3 object key.
    Example: originals/2025/01/550e8400-e29b-41d4-a716.jpg
    """
    from django.utils import timezone

    now = timezone.now()
    ext = _ALLOWED_EXTENSIONS.get(mime_type, "bin")
    uid = str(uuid.uuid4())
    return f"{prefix}/{now.year}/{now.month:02d}/{uid}.{ext}"


def generate_presigned_upload_url(
    *,
    s3_key: str,
    mime_type: str,
    expires_in: int = 900,  # 15 minutes
) -> str:
    """
    Generate a presigned PUT URL for direct-to-S3 client upload.

    In test/dev (USE_MINIO or no AWS config):
        Returns a dummy URL — no real S3 call.

    In production:
        Returns a real presigned S3 PUT URL.
    """
    bucket = getattr(settings, "AWS_STORAGE_BUCKET_NAME", None)

    if not bucket or getattr(settings, "USE_FAKE_S3", False):
        logger.debug("generate_presigned_upload_url: using fake URL (no S3 configured)")
        return f"https://fake-s3.example.com/{s3_key}?fake=true"

    try:
        import boto3

        endpoint = getattr(settings, "AWS_S3_ENDPOINT_URL", None)
        client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=getattr(settings, "AWS_ACCESS_KEY_ID", None),
            aws_secret_access_key=getattr(settings, "AWS_SECRET_ACCESS_KEY", None),
            region_name=getattr(settings, "AWS_S3_REGION_NAME", "us-east-1"),
        )
        return client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": bucket,
                "Key": s3_key,
                "ContentType": mime_type,
            },
            ExpiresIn=expires_in,
        )
    except Exception:
        logger.exception("Failed to generate presigned URL for key=%s", s3_key)
        raise


def build_cdn_url(s3_key: str) -> str:
    """Convert an S3 key to a CDN-served public URL."""
    cdn_domain = getattr(settings, "CDN_DOMAIN", None)
    if cdn_domain:
        return f"https://{cdn_domain}/{s3_key}"

    bucket = getattr(settings, "AWS_STORAGE_BUCKET_NAME", "")
    region = getattr(settings, "AWS_S3_REGION_NAME", "us-east-1")
    return f"https://{bucket}.s3.{region}.amazonaws.com/{s3_key}"


def delete_s3_object(s3_key: str) -> None:
    """Delete a single object from S3. Called on post/media delete."""
    bucket = getattr(settings, "AWS_STORAGE_BUCKET_NAME", None)
    if not bucket or getattr(settings, "USE_FAKE_S3", False):
        logger.debug("delete_s3_object: skipping (no S3 configured)")
        return

    try:
        import boto3

        client = boto3.client("s3")
        client.delete_object(Bucket=bucket, Key=s3_key)
        logger.info("Deleted S3 object: %s", s3_key)
    except Exception:
        logger.exception("Failed to delete S3 object: %s", s3_key)
