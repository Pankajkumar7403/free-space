"""
apps/common/moderation/services.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
High-level moderation service called by post/comment creation services.
"""
from __future__ import annotations

import logging
import uuid
from typing import Optional

from apps.common.moderation.constants import ModerationAction
from apps.common.moderation.text_filter import TextModerationFilter, TextModerationResult

logger = logging.getLogger(__name__)


def moderate_text(content: str, content_type: str = "post") -> TextModerationResult:
    """
    Run text moderation on user-submitted content.
    Called synchronously from post/comment services BEFORE saving to DB.

    Raises ValidationError if content should be blocked.
    Returns the result (may be WARN or PASS) so callers can act accordingly.
    """
    from core.monitoring.prometheus import MODERATION_ACTIONS

    result = TextModerationFilter.get_instance().check(content)

    MODERATION_ACTIONS.labels(
        action=result.action.value,
        severity=result.severity.value,
    ).inc()

    if result.action == ModerationAction.BLOCK:
        logger.warning(
            "moderation.text.blocked",
            extra={
                "content_type": content_type,
                "rule": result.matched_rule,
                "score": result.score,
            },
        )
        from django.core.exceptions import ValidationError
        raise ValidationError(
            "Your content violates our community guidelines and cannot be posted. "
            "Qommunity is a safe space - hate speech is not welcome here. 🏳️‍🌈"
        )

    if result.action == ModerationAction.WARN:
        logger.info(
            "moderation.text.warned",
            extra={"content_type": content_type, "rule": result.matched_rule},
        )

    return result


def check_for_crisis_content(content: str) -> bool:
    """
    Return True if content contains crisis keywords.
    The caller (post/comment creation) will surface mental health resources
    in the API response. Content is NOT blocked.
    """
    return TextModerationFilter.get_instance().check_crisis_keywords(content)


def moderate_image_async(media_id: uuid.UUID) -> None:
    """
    Queue an async Celery task to classify a media object for NSFW content.
    Called after media upload completes (status = READY).
    """
    from apps.common.moderation.tasks import classify_media_image
    classify_media_image.delay(str(media_id))


def get_crisis_resources(locale: str = "DEFAULT") -> dict:
    """Return crisis resources for the given locale."""
    from apps.common.safety.constants import CRISIS_RESOURCES
    return CRISIS_RESOURCES.get(locale) or CRISIS_RESOURCES.get("DEFAULT", {})
