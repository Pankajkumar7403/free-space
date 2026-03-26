"""
apps/notifications/tasks.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Async Celery tasks for FCM push and SendGrid email notifications.
All tasks are safe to retry — they are fully idempotent.
"""

from __future__ import annotations

import logging
import uuid

from celery import shared_task
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_fcm_push_notification(self, notification_id: str) -> None:
    """
    Fetch all active device tokens for the notification recipient,
    then call the FCM v1 HTTP API in a single batch request.
    """
    import requests

    from apps.notifications.models import Notification
    from apps.notifications.selectors import get_active_device_tokens

    try:
        notification = Notification.objects.select_related("actor", "recipient").get(
            id=uuid.UUID(notification_id)
        )
    except Notification.DoesNotExist:
        logger.warning("task.fcm.notification_not_found", extra={"id": notification_id})
        return

    tokens = list(
        get_active_device_tokens(notification.recipient_id).values_list(
            "token", flat=True
        )
    )
    if not tokens:
        return

    fcm_key = getattr(settings, "FCM_SERVER_KEY", "")
    if not fcm_key:
        logger.warning("task.fcm.no_server_key — skipping push")
        return

    payload = {
        "registration_ids": tokens,
        "notification": {
            "title": "Qommunity 🏳️‍🌈",
            "body": notification.message,
            "sound": "default",
        },
        "data": {
            "notification_id": str(notification.id),
            "notification_type": notification.notification_type,
            "target_id": (
                str(notification.object_id) if notification.object_id else ""
            ),
        },
        "priority": "high",
    }

    try:
        resp = requests.post(
            "https://fcm.googleapis.com/fcm/send",
            json=payload,
            headers={
                "Authorization": f"key={fcm_key}",
                "Content-Type": "application/json",
            },
            timeout=10,
        )
        resp.raise_for_status()
        logger.info(
            "task.fcm.sent",
            extra={
                "notification_id": notification_id,
                "token_count": len(tokens),
            },
        )
    except Exception as exc:
        logger.error(
            "task.fcm.failed",
            extra={"notification_id": notification_id, "error": str(exc)},
        )
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_notification(self, notification_id: str) -> None:
    """
    Send transactional email via SendGrid.
    Only fires when the user's NotificationPreference enables email for that type.
    """
    from apps.notifications.models import Notification

    try:
        notification = Notification.objects.select_related("recipient", "actor").get(
            id=uuid.UUID(notification_id)
        )
    except Notification.DoesNotExist:
        return

    recipient_email = getattr(notification.recipient, "email", None)
    if not recipient_email:
        return

    sg_key = getattr(settings, "SENDGRID_API_KEY", "")
    if not sg_key:
        logger.warning("task.email.no_sendgrid_key — skipping email")
        return

    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail

        mail = Mail(
            from_email=(
                settings.DEFAULT_FROM_EMAIL,
                getattr(settings, "EMAIL_SENDER_NAME", "Qommunity"),
            ),
            to_emails=recipient_email,
            subject="New notification from Qommunity 🏳️‍🌈",
            html_content=(
                f"<p>{notification.message}</p>"
                f"<p><a href='https://qommunity.app/notifications'>"
                f"View all notifications</a></p>"
            ),
        )
        sg = sendgrid.SendGridAPIClient(api_key=sg_key)
        sg.send(mail)
        logger.info(
            "task.email.sent",
            extra={"notification_id": notification_id, "to": recipient_email},
        )
    except Exception as exc:
        logger.error(
            "task.email.failed",
            extra={"notification_id": notification_id, "error": str(exc)},
        )
        raise self.retry(exc=exc)


@shared_task
def cleanup_old_notifications() -> None:
    """
    Periodic task (daily at 3 AM via CELERY_BEAT_SCHEDULE).
    Delete read notifications older than 90 days to bound the DB table size.
    """
    from datetime import timedelta

    from django.utils import timezone

    from apps.notifications.models import Notification

    cutoff = timezone.now() - timedelta(days=90)
    count, _ = Notification.objects.filter(
        is_read=True,
        created_at__lt=cutoff,
    ).delete()
    logger.info("task.cleanup_notifications.done", extra={"deleted": count})
