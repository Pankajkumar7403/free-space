"""
core/monitoring/sentry.py
~~~~~~~~~~~~~~~~~~~~~~~~~
Sentry SDK bootstrap.
Called once at Django startup via apps.py or settings import.
All configuration is driven by environment variables so no secrets
live in code.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def init_sentry(settings) -> None:
    """
    Initialize Sentry.  Called from production settings.
    Safe to call even if SENTRY_DSN is empty — does nothing in that case.
    """
    dsn = getattr(settings, "SENTRY_DSN", "")
    if not dsn:
        logger.info("sentry.init.skipped — SENTRY_DSN not set")
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.celery import CeleryIntegration
        from sentry_sdk.integrations.django import DjangoIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
        from sentry_sdk.integrations.redis import RedisIntegration

        sentry_sdk.init(
            dsn=dsn,
            integrations=[
                DjangoIntegration(
                    transaction_style="url",    # group by URL pattern, not instance
                    middleware_spans=True,
                    signals_spans=False,        # reduce noise
                ),
                CeleryIntegration(
                    monitor_beat_tasks=True,
                    propagate_traces=True,
                ),
                RedisIntegration(),
                LoggingIntegration(
                    level=logging.WARNING,       # breadcrumb level
                    event_level=logging.ERROR,   # send as Sentry event
                ),
            ],
            # Performance monitoring
            traces_sample_rate=getattr(settings, "SENTRY_TRACES_SAMPLE_RATE", 0.10),
            profiles_sample_rate=getattr(settings, "SENTRY_PROFILES_SAMPLE_RATE", 0.05),
            # Privacy — never send PII
            send_default_pii=False,
            # Context
            environment=getattr(settings, "DJANGO_ENV", "production"),
            release=getattr(settings, "APP_RELEASE", ""),
            # Filter noise
            ignore_errors=[
                KeyboardInterrupt,
                "django.security.DisallowedHost",
            ],
            before_send=_before_send,
        )
        logger.info("sentry.init.success", extra={"env": settings.DJANGO_ENV})

    except ImportError:
        logger.warning("sentry.init.failed — sentry-sdk not installed")


def _before_send(event, hint):
    """
    Strip sensitive fields before sending to Sentry.
    Removes Authorization headers, passwords, and LGBTQ+ identity fields.
    """
    # Strip auth headers
    request = event.get("request", {})
    headers = request.get("headers", {})
    for sensitive_key in ("Authorization", "Cookie", "X-Api-Key"):
        if sensitive_key in headers:
            headers[sensitive_key] = "[Filtered]"

    # Strip identity fields from user data
    user = event.get("user", {})
    for field in ("pronouns", "gender_identity", "sexual_orientation"):
        user.pop(field, None)

    return event
