from __future__ import annotations

import logging

from apps.common.moderation.constants import ModerationAction
from apps.common.moderation.text_filter import TextModerationFilter, TextModerationResult

logger = logging.getLogger(__name__)


def moderate_text(content: str, content_type: str = "post") -> TextModerationResult:
    result = TextModerationFilter.get_instance().check(content)
    if result.action == ModerationAction.BLOCK:
        logger.warning(
            "moderation.text.blocked",
            extra={"content_type": content_type, "rule": result.matched_rule},
        )
        from django.core.exceptions import ValidationError
        raise ValidationError(
            "Your content violates our community guidelines."
        )
    if result.action == ModerationAction.WARN:
        logger.info(
            "moderation.text.warned",
            extra={"content_type": content_type, "rule": result.matched_rule},
        )
    return result


def check_for_crisis_content(content: str) -> bool:
    return TextModerationFilter.get_instance().check_crisis_keywords(content)


def get_crisis_resources(locale: str = "DEFAULT") -> dict:
    from apps.common.safety.constants import CRISIS_RESOURCES
    return CRISIS_RESOURCES.get(locale) or CRISIS_RESOURCES.get("DEFAULT", {})
