"""
All messaging domain constants, enums, and key patterns.
Single source of truth — import from here everywhere.
"""

from django.db import models


class ConversationType(models.TextChoices):
    DIRECT = "direct", "Direct Message"
    GROUP = "group", "Group Chat"


class MessageType(models.TextChoices):
    TEXT = "text", "Text"
    MEDIA = "media", "Media Attachment"
    SYSTEM = "system", "System Event"


class ParticipantRole(models.TextChoices):
    ADMIN = "admin", "Admin"
    MEMBER = "member", "Member"


CONVERSATION_GROUP_PREFIX = "conversation__"


def get_conversation_group(conversation_id) -> str:
    return f"{CONVERSATION_GROUP_PREFIX}{conversation_id}"


TYPING_KEY = "messaging:typing:{conversation_id}:{user_id}"
TYPING_TTL_SECONDS = 8

UNREAD_CACHE_KEY = "messaging:unread:{user_id}"
UNREAD_CACHE_TTL = 300

PRESENCE_KEY = "messaging:presence:{user_id}"
PRESENCE_TTL_SECONDS = 60

MAX_GROUP_PARTICIPANTS = 100
MAX_MESSAGE_LENGTH = 5_000
MAX_GROUP_NAME_LENGTH = 100
MESSAGES_PAGE_SIZE = 30
CONVERSATIONS_PAGE_SIZE = 20

ALLOWED_EMOJI_REACTIONS = frozenset(
    {
        "❤️",
        "🏳️‍🌈",
        "😂",
        "😮",
        "😢",
        "😡",
        "👍",
        "👎",
        "🔥",
        "✨",
        "💜",
        "🎉",
        "🌈",
    }
)

