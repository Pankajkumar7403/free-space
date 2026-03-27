from __future__ import annotations

import logging
import uuid

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_gdpr_export(self, user_id: str, job_id: str) -> None:
    """
    Generate data export ZIP and email the download link to the user.
    """
    from apps.common.gdpr.exporters import export_user_data
    from core.monitoring.prometheus import GDPR_EXPORTS

    try:
        download_url = export_user_data(uuid.UUID(user_id))
        _send_export_ready_email(user_id, download_url)
        GDPR_EXPORTS.labels(status="completed").inc()
        logger.info(
            "gdpr.export.completed", extra={"user_id": user_id, "job_id": job_id}
        )
    except Exception as exc:
        GDPR_EXPORTS.labels(status="failed").inc()
        logger.error(
            "gdpr.export.failed", extra={"user_id": user_id, "error": str(exc)}
        )
        raise self.retry(exc=exc)


@shared_task
def cleanup_s3_media(keys: list[str]) -> None:
    """Batch-delete S3 objects left over from an account deletion."""
    if not keys:
        return
    from apps.media.storage import delete_s3_object

    for key in keys:
        delete_s3_object(key)
    logger.info("gdpr.s3_cleanup.done", extra={"count": len(keys)})


def _send_export_ready_email(user_id: str, download_url: str) -> None:
    from django.conf import settings

    from apps.users.models import User

    try:
        user = User.objects.get(id=uuid.UUID(user_id))
        sg_key = getattr(settings, "SENDGRID_API_KEY", "")
        if not sg_key:
            return

        import sendgrid
        from sendgrid.helpers.mail import Mail

        sg = sendgrid.SendGridAPIClient(api_key=sg_key)
        mail = Mail(
            from_email=settings.DEFAULT_FROM_EMAIL,
            to_emails=user.email,
            subject="Your Qommunity data export is ready",
            html_content=(
                f"<p>Hi {user.username},</p>"
                f"<p>Your data export is ready. "
                f'<a href="{download_url}">Download your data</a></p>'
                f"<p>This link expires in 24 hours.</p>"
                f"<p>🏳️‍🌈 The Qommunity Team</p>"
            ),
        )
        sg.send(mail)
    except Exception as exc:
        logger.warning("gdpr.export_email.failed", extra={"error": str(exc)})
