"""
Conversation
    A thread between 2+ users (direct or group).
    Uses last_message_preview (denormalized text) + last_message_at
    instead of a FK to Message — avoids circular FK dependency.

ConversationParticipant
    Explicit through model for the Conversation ↔ User M2M.
    Stores per-participant metadata: role, last_seen_at, is_muted.
    last_seen_at drives the unread count.

Message
    A single message in a conversation.
    Supports text, media attachments, and reply threading.
    Soft-deleted (is_deleted=True, content cleared).

MessageReaction
    Emoji reactions on messages.
    unique_together: (message, user, emoji) — one reaction type per user.
"""

from django.db import models

from apps.messaging.constants import (
    ConversationType,
    MAX_GROUP_NAME_LENGTH,
    MAX_MESSAGE_LENGTH,
    MessageType,
    ParticipantRole,
)
from core.database.base_model import BaseModel


class Conversation(BaseModel):
    conversation_type = models.CharField(
        max_length=10,
        choices=ConversationType.choices,
        default=ConversationType.DIRECT,
        db_index=True,
    )
    name = models.CharField(
        max_length=MAX_GROUP_NAME_LENGTH,
        blank=True,
        help_text="Group name — empty for direct conversations.",
    )
    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_conversations",
    )

    last_message_preview = models.CharField(max_length=100, blank=True)
    last_message_at = models.DateTimeField(null=True, blank=True, db_index=True)
    last_message_sender = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    class Meta:
        db_table = "conversations"
        ordering = ["-last_message_at"]
        indexes = [
            models.Index(
                fields=["-last_message_at"],
                name="conv_last_msg_idx",
            )
        ]

    def __str__(self) -> str:
        if self.conversation_type == ConversationType.GROUP:
            return f"Group({self.name or self.id})"
        return f"Direct({self.id})"

    @property
    def is_direct(self) -> bool:
        return self.conversation_type == ConversationType.DIRECT

    @property
    def is_group(self) -> bool:
        return self.conversation_type == ConversationType.GROUP


class ConversationParticipant(BaseModel):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="participants",
        db_index=True,
    )
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="conversation_participants",
        db_index=True,
    )
    role = models.CharField(
        max_length=10,
        choices=ParticipantRole.choices,
        default=ParticipantRole.MEMBER,
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(null=True, blank=True, db_index=True)
    is_muted = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)

    class Meta:
        db_table = "conversation_participants"
        unique_together = [("conversation", "user")]

    def __str__(self) -> str:
        return f"Participant({self.user_id} in {self.conversation_id})"


class Message(BaseModel):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
        db_index=True,
    )
    sender = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="sent_messages",
    )
    content = models.TextField(max_length=MAX_MESSAGE_LENGTH, blank=True)
    message_type = models.CharField(
        max_length=10,
        choices=MessageType.choices,
        default=MessageType.TEXT,
        db_index=True,
    )
    media = models.ForeignKey(
        "posts.Media",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="message_attachments",
    )
    reply_to = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="replies",
    )

    class Meta:
        db_table = "messages"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["conversation", "-created_at"],
                name="msg_conv_created_idx",
            )
        ]

    def __str__(self) -> str:
        preview = self.content[:40] if self.content else "[media]"
        return f"Message({self.id}) from {self.sender_id}: {preview}"

    def get_display_content(self) -> str:
        if self.is_deleted:
            return "This message was deleted."
        return self.content


class MessageReaction(BaseModel):
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="reactions",
        db_index=True,
    )
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="message_reactions",
    )
    emoji = models.CharField(max_length=10)

    class Meta:
        db_table = "message_reactions"
        unique_together = [("message", "user", "emoji")]
        indexes = [
            models.Index(
                fields=["message"],
                name="reaction_message_idx",
            )
        ]

    def __str__(self) -> str:
        return f"Reaction({self.emoji} by {self.user_id} on {self.message_id})"

