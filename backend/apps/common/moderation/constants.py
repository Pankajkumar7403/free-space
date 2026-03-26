"""
Content moderation constants.

IMPORTANT: The full anti-LGBTQ+ slur blocklist is loaded from a
secure environment variable / config file - NOT hardcoded here.
See docs/moderation_setup.md for configuration instructions.
"""

from enum import StrEnum


class ModerationAction(StrEnum):
    BLOCK = "block"  # Reject content entirely
    WARN = "warn"  # Flag for human review, allow posting
    PASS = "pass"  # Content is clean


class ModerationSeverity(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ContentType(StrEnum):
    POST = "post"
    COMMENT = "comment"
    BIO = "bio"
    MESSAGE = "message"


# Threshold above which content is auto-blocked (0-1 score)
BLOCK_SCORE_THRESHOLD = 0.85
WARN_SCORE_THRESHOLD = 0.50

# NSFW image detection confidence threshold
NSFW_BLOCK_CONFIDENCE = 0.90
NSFW_WARN_CONFIDENCE = 0.70

# Crisis keyword triggers -> surface mental health resources
# Full list loaded from CRISIS_KEYWORDS env var
CRISIS_KEYWORDS_DEFAULT = frozenset(
    {
        "suicide",
        "kill myself",
        "end it all",
        "want to die",
        "don't want to live",
        "self harm",
        "hurt myself",
    }
)

# Minimum content length to run ML classifier (skip very short text)
ML_MIN_TEXT_LENGTH = 20
