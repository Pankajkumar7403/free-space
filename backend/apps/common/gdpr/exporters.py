"""
apps/common/gdpr/exporters.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Collects all data belonging to a user and packages it as a
JSON zip file uploaded to S3.  Returns a presigned download URL.

Article 20 GDPR - Right to data portability.
"""
from __future__ import annotations

import io
import json
import logging
import uuid
import zipfile
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def export_user_data(user_id: uuid.UUID) -> str:
    """
    Collect all user data, zip as JSON, upload to S3.
    Returns a presigned S3 URL valid for 24 hours.
    """
    data = {
        "export_date":     datetime.now(tz=timezone.utc).isoformat(),
        "export_version":  "1.0",
        "profile":         _export_profile(user_id),
        "posts":           _export_posts(user_id),
        "comments":        _export_comments(user_id),
        "likes":           _export_likes(user_id),
        "follows":         _export_follows(user_id),
        "notifications":   _export_notifications(user_id),
        "device_tokens":   _export_device_tokens(user_id),
    }

    json_bytes = json.dumps(data, indent=2, default=str).encode("utf-8")

    # Package in zip
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("qommunity_data_export.json", json_bytes)
    zip_buffer.seek(0)

    # Upload to S3
    s3_key = _upload_export_to_s3(user_id, zip_buffer.read())

    # Return presigned URL (24h)
    from apps.media.storage import S3Storage
    from django.conf import settings

    storage = S3Storage.get_instance()
    import boto3
    client = boto3.client(
        "s3",
        endpoint_url=getattr(settings, "AWS_S3_ENDPOINT_URL", None),
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=getattr(settings, "AWS_S3_REGION_NAME", "us-east-1"),
    )
    url = client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.AWS_STORAGE_BUCKET_NAME, "Key": s3_key},
        ExpiresIn=86400,   # 24 hours
    )
    logger.info("gdpr.export.uploaded", extra={"user_id": str(user_id), "key": s3_key})
    return url


# -- Private collectors -------------------------------------------------------

def _export_profile(user_id: uuid.UUID) -> dict:
    from apps.users.models import User
    try:
        u = User.objects.get(id=user_id)
        return {
            "id":               str(u.id),
            "username":         u.username,
            "email":            u.email,
            "display_name":     getattr(u, "display_name", ""),
            "bio":              getattr(u, "bio", ""),
            "pronouns":         getattr(u, "pronouns", []),
            "gender_identity":  getattr(u, "gender_identity", ""),
            "sexual_orientation": getattr(u, "sexual_orientation", ""),
            "account_privacy":  getattr(u, "account_privacy", ""),
            "created_at":       u.date_joined.isoformat() if hasattr(u, "date_joined") else "",
        }
    except Exception:
        return {}


def _export_posts(user_id: uuid.UUID) -> list:
    from apps.posts.models import Post
    return [
        {
            "id":          str(p.id),
            "content":     p.content,
            "visibility":  p.visibility,
            "location":    getattr(p, "location", getattr(p, "location_name", "")),
            "hashtags":    list(p.hashtags.values_list("name", flat=True)),
            "like_count":  getattr(p, "like_count", 0),
            "created_at":  p.created_at.isoformat(),
        }
        for p in Post.all_objects.filter(author_id=user_id).prefetch_related("hashtags")
    ]


def _export_comments(user_id: uuid.UUID) -> list:
    from apps.comments.models import Comment
    return [
        {
            "id":         str(c.id),
            "post_id":    str(c.post_id),
            "content":    c.content,
            "created_at": c.created_at.isoformat(),
        }
        for c in Comment.all_objects.filter(author_id=user_id)
    ]


def _export_likes(user_id: uuid.UUID) -> list:
    from apps.likes.models import Like
    return [
        {
            "id":           str(lk.id),
            "target_type":  str(lk.content_type),
            "target_id":    str(lk.object_id),
            "created_at":   lk.created_at.isoformat(),
        }
        for lk in Like.objects.filter(user_id=user_id)
    ]


def _export_follows(user_id: uuid.UUID) -> dict:
    from apps.users.models import Follow
    following = list(
        Follow.objects.filter(follower_id=user_id).values_list("following__username", flat=True)
    )
    followers = list(
        Follow.objects.filter(following_id=user_id).values_list("follower__username", flat=True)
    )
    return {"following": following, "followers": followers}


def _export_notifications(user_id: uuid.UUID) -> list:
    from apps.notifications.models import Notification
    return [
        {
            "id":                str(n.id),
            "notification_type": n.notification_type,
            "message":           n.message,
            "is_read":           n.is_read,
            "created_at":        n.created_at.isoformat(),
        }
        for n in Notification.objects.filter(recipient_id=user_id)
    ]


def _export_device_tokens(user_id: uuid.UUID) -> list:
    from apps.notifications.models import DeviceToken
    return [
        {"platform": t.platform, "is_active": t.is_active}
        for t in DeviceToken.objects.filter(user_id=user_id)
    ]


def _upload_export_to_s3(user_id: uuid.UUID, data: bytes) -> str:
    import boto3
    import io
    from django.conf import settings

    key = f"gdpr-exports/{user_id}/data_export.zip"
    client = boto3.client(
        "s3",
        endpoint_url=getattr(settings, "AWS_S3_ENDPOINT_URL", None),
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )
    client.put_object(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Key=key,
        Body=data,
        ContentType="application/zip",
        ServerSideEncryption="AES256",
    )
    return key
