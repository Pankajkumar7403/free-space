"""
apps/common/tests/test_moderation.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Tests for content moderation: text filter, image classifier, services.
No DB required for most tests - all moderation logic is stateless.
"""

from unittest.mock import patch

import pytest
from django.test import override_settings

# -- TextModerationFilter -----------------------------------------------------


@pytest.fixture(autouse=True)
def reset_text_filter_singleton():
    """
    Reset the TextModerationFilter singleton before each test
    so blocklist changes from @override_settings take effect.
    """
    from apps.common.moderation.text_filter import TextModerationFilter

    TextModerationFilter._instance = None
    yield
    TextModerationFilter._instance = None


class TestTextModerationFilterCleanContent:

    def test_empty_string_returns_pass(self):
        from apps.common.moderation.constants import ModerationAction
        from apps.common.moderation.text_filter import TextModerationFilter

        result = TextModerationFilter.get_instance().check("")
        assert result.action == ModerationAction.PASS

    def test_whitespace_only_returns_pass(self):
        from apps.common.moderation.constants import ModerationAction
        from apps.common.moderation.text_filter import TextModerationFilter

        result = TextModerationFilter.get_instance().check("   ")
        assert result.action == ModerationAction.PASS

    def test_clean_content_returns_pass(self):
        from apps.common.moderation.constants import ModerationAction
        from apps.common.moderation.text_filter import TextModerationFilter

        result = TextModerationFilter.get_instance().check(
            "Hello! Happy Pride Month! 🏳️‍🌈 #LGBTQ #community"
        )
        assert result.action == ModerationAction.PASS

    def test_pass_result_has_zero_score(self):
        from apps.common.moderation.text_filter import TextModerationFilter

        result = TextModerationFilter.get_instance().check("Just a normal post.")
        assert result.score == 0.0


class TestTextModerationFilterBlocklist:

    @override_settings(MODERATION_BLOCKLIST=["badword123", "hatephrase456"])
    def test_exact_blocklist_match_returns_block(self):
        from apps.common.moderation.constants import ModerationAction
        from apps.common.moderation.text_filter import TextModerationFilter

        result = TextModerationFilter.get_instance().check(
            "This contains badword123 here"
        )
        assert result.action == ModerationAction.BLOCK

    @override_settings(MODERATION_BLOCKLIST=["badword123"])
    def test_block_result_high_severity(self):
        from apps.common.moderation.constants import ModerationSeverity
        from apps.common.moderation.text_filter import TextModerationFilter

        result = TextModerationFilter.get_instance().check("badword123 in text")
        assert result.severity == ModerationSeverity.HIGH

    @override_settings(MODERATION_BLOCKLIST=["badword123"])
    def test_block_result_score_is_1(self):
        from apps.common.moderation.text_filter import TextModerationFilter

        result = TextModerationFilter.get_instance().check("badword123")
        assert result.score == 1.0

    @override_settings(MODERATION_BLOCKLIST=["badword123"])
    def test_block_result_has_matched_rule(self):
        from apps.common.moderation.text_filter import TextModerationFilter

        result = TextModerationFilter.get_instance().check("badword123")
        assert result.matched_rule is not None

    @override_settings(MODERATION_BLOCKLIST=["badword123"])
    def test_case_insensitive_blocking(self):
        """BADWORD123 must also be blocked (normalisation lowercases it)."""
        from apps.common.moderation.constants import ModerationAction
        from apps.common.moderation.text_filter import TextModerationFilter

        result = TextModerationFilter.get_instance().check("BADWORD123 in uppercase")
        assert result.action == ModerationAction.BLOCK

    @override_settings(MODERATION_BLOCKLIST=["badword123"])
    def test_evasion_with_symbols_blocked(self):
        """b.a.d.w.o.r.d.1.2.3 must not bypass the filter."""
        from apps.common.moderation.constants import ModerationAction
        from apps.common.moderation.text_filter import TextModerationFilter

        result = TextModerationFilter.get_instance().check("b.a.d.w.o.r.d.1.2.3")
        assert result.action == ModerationAction.BLOCK


class TestTextModerationFilterCrisisKeywords:

    def test_crisis_keyword_returns_warn(self):
        from apps.common.moderation.constants import ModerationAction
        from apps.common.moderation.text_filter import TextModerationFilter

        result = TextModerationFilter.get_instance().check(
            "I don't want to live anymore"
        )
        assert result.action == ModerationAction.WARN

    def test_crisis_result_medium_severity(self):
        from apps.common.moderation.constants import ModerationSeverity
        from apps.common.moderation.text_filter import TextModerationFilter

        result = TextModerationFilter.get_instance().check("I want to die")
        assert result.severity == ModerationSeverity.MEDIUM

    def test_crisis_rule_identified(self):
        from apps.common.moderation.text_filter import TextModerationFilter

        result = TextModerationFilter.get_instance().check("I want to die")
        assert result.matched_rule == "crisis_keyword"

    @override_settings(CRISIS_KEYWORDS=["customcrisisword"])
    def test_custom_crisis_keywords_from_settings(self):
        from apps.common.moderation.constants import ModerationAction
        from apps.common.moderation.text_filter import TextModerationFilter

        result = TextModerationFilter.get_instance().check(
            "I am feeling customcrisisword today"
        )
        assert result.action == ModerationAction.WARN


class TestCheckForCrisisContent:

    def test_returns_true_for_crisis_content(self):
        from apps.common.moderation.services import check_for_crisis_content

        assert check_for_crisis_content("I don't want to live") is True

    def test_returns_false_for_clean_content(self):
        from apps.common.moderation.services import check_for_crisis_content

        assert check_for_crisis_content("Having a great day! #pride") is False

    def test_empty_string_returns_false(self):
        from apps.common.moderation.services import check_for_crisis_content

        assert check_for_crisis_content("") is False


class TestModerateTextService:

    @override_settings(MODERATION_BLOCKLIST=["badword123"])
    def test_raises_validation_error_on_block(self):
        from django.core.exceptions import ValidationError

        from apps.common.moderation.services import moderate_text

        with pytest.raises(ValidationError):
            moderate_text("This has badword123 in it")

    def test_returns_result_for_clean_content(self):
        from apps.common.moderation.constants import ModerationAction
        from apps.common.moderation.services import moderate_text

        result = moderate_text("A beautiful post about love and pride 🏳️‍🌈")
        assert result.action == ModerationAction.PASS

    def test_validation_error_message_is_friendly(self):
        """Error message must not shame the user, just explain the policy."""
        from django.core.exceptions import ValidationError

        from apps.common.moderation.services import moderate_text

        with override_settings(MODERATION_BLOCKLIST=["testslur999"]):
            with pytest.raises(ValidationError) as exc_info:
                moderate_text("testslur999")
        assert "community guidelines" in str(exc_info.value).lower()

    def test_warn_content_does_not_raise(self):
        """Crisis content returns WARN - must NOT raise ValidationError."""
        from apps.common.moderation.constants import ModerationAction
        from apps.common.moderation.services import moderate_text

        result = moderate_text("I want to die")
        assert result.action == ModerationAction.WARN



# -- Crisis resources ---------------------------------------------------------


class TestGetCrisisResources:

    def test_returns_dict_for_default_locale(self):
        from apps.common.moderation.services import get_crisis_resources

        resources = get_crisis_resources("DEFAULT")
        assert isinstance(resources, dict)
        assert len(resources) > 0

    def test_returns_us_resources(self):
        from apps.common.moderation.services import get_crisis_resources

        resources = get_crisis_resources("US")
        assert isinstance(resources, dict)
        assert len(resources) > 0

    def test_unknown_locale_falls_back_to_default(self):
        from apps.common.moderation.services import get_crisis_resources

        resources = get_crisis_resources("ZZ")
        assert resources is not None
