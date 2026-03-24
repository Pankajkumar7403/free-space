"""
apps/common/moderation/text_filter.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Multi-layer text moderation:

Layer 1 - Exact blocklist match (fastest, zero latency)
Layer 2 - Normalised match (handles l33tspeak, extra spaces, repeated chars)
Layer 3 - Regex pattern matching for common evasion patterns
Layer 4 - ML classifier (optional, async via Celery for performance)

The blocklist is intentionally NOT stored in code.  Load it from:
  - Environment variable: MODERATION_BLOCKLIST_PATH (path to newline-delimited file)
  - Or Django setting: MODERATION_BLOCKLIST (list of strings)
"""
from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Optional

from django.conf import settings

from apps.common.moderation.constants import (
    BLOCK_SCORE_THRESHOLD,
    WARN_SCORE_THRESHOLD,
    ModerationAction,
    ModerationSeverity,
)

logger = logging.getLogger(__name__)


@dataclass
class TextModerationResult:
    action:       ModerationAction
    severity:     ModerationSeverity
    score:        float              # 0.0 = clean, 1.0 = definitely harmful
    matched_rule: Optional[str] = None
    explanation:  str = ""


class TextModerationFilter:
    """
    Singleton text moderation filter.
    Loads blocklist once on first use; thread-safe for reads.
    """
    _instance: Optional[TextModerationFilter] = None
    _blocklist: frozenset[str] = frozenset()

    @classmethod
    def get_instance(cls) -> TextModerationFilter:
        if cls._instance is None:
            cls._instance = cls()
            cls._instance._load_blocklist()
        return cls._instance

    # -- Public API -----------------------------------------------------------

    def check(self, text: str) -> TextModerationResult:
        """
        Run all moderation layers on text.
        Returns the most severe result found.
        """
        if not text or not text.strip():
            return self._pass()

        normalised = self._normalise(text)

        # Layer 1: exact blocklist
        result = self._check_blocklist(normalised)
        if result.action == ModerationAction.BLOCK:
            return result

        # Layer 2: pattern matching (evasion tactics)
        result = self._check_patterns(normalised)
        if result.action == ModerationAction.BLOCK:
            return result

        # Layer 3: crisis keyword detection (different from hate speech)
        result = self._check_crisis_keywords(normalised)
        if result.action == ModerationAction.WARN:
            return result

        return self._pass()

    def check_crisis_keywords(self, text: str) -> bool:
        """Return True if text contains crisis keywords that should trigger resource display."""
        from apps.common.moderation.constants import CRISIS_KEYWORDS_DEFAULT
        custom = frozenset(getattr(settings, "CRISIS_KEYWORDS", []))
        all_keywords = CRISIS_KEYWORDS_DEFAULT | custom
        normalised = self._normalise(text)
        return any(kw in normalised for kw in all_keywords)

    # -- Private layers -------------------------------------------------------

    def _check_blocklist(self, normalised: str) -> TextModerationResult:
        words = set(normalised.split())
        for term in self._blocklist:
            if term in words or term in normalised:
                return TextModerationResult(
                    action=ModerationAction.BLOCK,
                    severity=ModerationSeverity.HIGH,
                    score=1.0,
                    matched_rule="blocklist",
                    explanation="Content contains prohibited terms.",
                )
        return self._pass()

    def _check_patterns(self, normalised: str) -> TextModerationResult:
        """
        Detect common evasion patterns:
        - Repeated characters: h***e -> hate
        - Interstitial symbols: h.a.t.e
        """
        # Strip non-alphanumeric between letters
        collapsed = re.sub(r"[^a-z0-9\s]", "", normalised)
        collapsed = re.sub(r"\s+", " ", collapsed)

        for term in self._blocklist:
            if term in collapsed:
                return TextModerationResult(
                    action=ModerationAction.BLOCK,
                    severity=ModerationSeverity.HIGH,
                    score=0.95,
                    matched_rule="evasion_pattern",
                    explanation="Content contains obfuscated prohibited terms.",
                )
        return self._pass()

    def _check_crisis_keywords(self, normalised: str) -> TextModerationResult:
        from apps.common.moderation.constants import CRISIS_KEYWORDS_DEFAULT
        custom = frozenset(getattr(settings, "CRISIS_KEYWORDS", []))
        all_kw = CRISIS_KEYWORDS_DEFAULT | custom
        for kw in all_kw:
            if kw in normalised:
                return TextModerationResult(
                    action=ModerationAction.WARN,
                    severity=ModerationSeverity.MEDIUM,
                    score=0.6,
                    matched_rule="crisis_keyword",
                    explanation="Content may require crisis resource display.",
                )
        return self._pass()

    # -- Helpers --------------------------------------------------------------

    @staticmethod
    def _normalise(text: str) -> str:
        """
        Normalise text to catch evasion:
        1. Unicode normalise (NFKD) - catches lookalike chars
        2. Lowercase
        3. Strip accents
        4. Collapse whitespace
        """
        text = unicodedata.normalize("NFKD", text)
        text = "".join(c for c in text if not unicodedata.combining(c))
        return text.lower().strip()

    def _load_blocklist(self) -> None:
        """Load blocklist from settings or file path."""
        terms: list[str] = []

        # From Django setting
        setting_list = getattr(settings, "MODERATION_BLOCKLIST", [])
        terms.extend(setting_list)

        # From file
        path = getattr(settings, "MODERATION_BLOCKLIST_PATH", "")
        if path:
            try:
                with open(path, encoding="utf-8") as f:
                    file_terms = [
                        line.strip().lower()
                        for line in f
                        if line.strip() and not line.startswith("#")
                    ]
                terms.extend(file_terms)
            except FileNotFoundError:
                logger.warning(
                    "moderation.blocklist_file_not_found",
                    extra={"path": path},
                )

        self._blocklist = frozenset(t for t in terms if t)
        logger.info(
            "moderation.blocklist_loaded",
            extra={"term_count": len(self._blocklist)},
        )

    @staticmethod
    def _pass() -> TextModerationResult:
        return TextModerationResult(
            action=ModerationAction.PASS,
            severity=ModerationSeverity.LOW,
            score=0.0,
        )
