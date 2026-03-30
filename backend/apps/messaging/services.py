"""
All messaging domain mutations.
Views, consumers, and Kafka handlers call these — never the models directly.
"""

from __future__ import annotations

import logging
import uuid
from typing import Optional

from django.db import transaction
from django.utils import timezone

from apps.messaging.constants import (
    ALLOWED_EMOJI_REACTIONS,
    MAX_GROUP_PARTICIPANTS,
    ConversationType,
    MessageType,
    ParticipantRole,
    get_conversation_group,
)
from apps.messaging.exceptions import (
    BlockedUserMessageError,
    GroupConversationRequiredError,
    InvalidEmojiError,
    MaxParticipantsReachedError,
    MessageDeleteForbiddenError,
    NotAParticipantError,
    NotConversationAdminError,
)
from apps.messaging.models import Conversation, ConversationParticipant, Message, MessageReaction
from apps.messaging.selectors import get_conversation_by_id, get_message_by_id

logger = logging.getLogger(__name__)


def create_direct_conversation(
    *,
    user1_id: uuid.UUID,
    user2_id: uuid.UUID,
) -> tuple[Conversation, bool]:
    from apps.common.safety.services import is_blocked

    if is_blocked(viewer_id=user1_id, target_id=user2_id):
        raise BlockedUserMessageError()

    existing = (
        Conversation.objects.filter(
            conversation_type=ConversationType.DIRECT,
            participants__user_id=user1_id,
        )
        .filter(participants__user_id=user2_id)
        .first()
    )
    if existing:
        return existing, False

    with transaction.atomic():
        conversation = Conversation.objects.create(
            conversation_type=ConversationType.DIRECT,
            created_by_id=user1_id,
        )
        ConversationParticipant.objects.bulk_create(
            [
                ConversationParticipant(
                    conversation=conversation,
                    user_id=user1_id,
                    role=ParticipantRole.ADMIN,
                ),
                ConversationParticipant(
                    conversation=conversation,
                    user_id=user2_id,
                    role=ParticipantRole.MEMBER,
                ),
            ]
        )
        _send_system_message(conversation, "Conversation started.")

    return conversation, True


def create_group_conversation(
    *,
    creator_id: uuid.UUID,
    participant_ids: list[uuid.UUID],
    name: str,
) -> Conversation:
    all_participant_ids = list({creator_id} | set(participant_ids))

    if len(all_participant_ids) > MAX_GROUP_PARTICIPANTS:
        raise MaxParticipantsReachedError()

    with transaction.atomic():
        conversation = Conversation.objects.create(
            conversation_type=ConversationType.GROUP,
            name=name.strip(),
            created_by_id=creator_id,
        )
        participants = [
            ConversationParticipant(
                conversation=conversation,
                user_id=uid,
                role=ParticipantRole.ADMIN if uid == creator_id else ParticipantRole.MEMBER,
            )
            for uid in all_participant_ids
        ]
        ConversationParticipant.objects.bulk_create(participants)
        _send_system_message(conversation, f"Group '{name}' created.")

    logger.info(
        "messaging.group_created",
        extra={
            "conversation_id": str(conversation.id),
            "creator_id": str(creator_id),
            "participant_count": len(all_participant_ids),
        },
    )
    return conversation


def send_message(
    *,
    conversation_id: uuid.UUID,
    sender_id: uuid.UUID,
    content: str,
    media_id: Optional[uuid.UUID] = None,
    reply_to_id: Optional[uuid.UUID] = None,
) -> Message:
    conversation = get_conversation_by_id(conversation_id)

    if not _is_participant(conversation_id, sender_id):
        raise NotAParticipantError()

    content = (content or "").strip()
    if not content and not media_id:
        from django.core.exceptions import ValidationError

        raise ValidationError("Message must have content or a media attachment.")

    if content:
        from apps.common.moderation.services import moderate_text

        moderate_text(content, content_type="message")

    msg_type = MessageType.MEDIA if media_id and not content else MessageType.TEXT

    with transaction.atomic():
        message = Message.objects.create(
            conversation=conversation,
            sender_id=sender_id,
            content=content,
            message_type=msg_type,
            media_id=media_id,
            reply_to_id=reply_to_id,
        )

        preview = content[:97] + "…" if len(content) > 100 else content
        if not preview:
            preview = "[media]"

        Conversation.objects.filter(id=conversation_id).update(
            last_message_preview=preview,
            last_message_at=message.created_at,
            last_message_sender_id=sender_id,
        )

    logger.debug(
        "messaging.message_sent",
        extra={
            "message_id": str(message.id),
            "conversation_id": str(conversation_id),
            "sender_id": str(sender_id),
        },
    )
    return message


def delete_message(*, message_id: uuid.UUID, user_id: uuid.UUID) -> Message:
    message = get_message_by_id(message_id)
    if str(message.sender_id) != str(user_id):
        raise MessageDeleteForbiddenError()

    message.is_deleted = True
    message.deleted_at = timezone.now()
    message.content = ""
    message.save(update_fields=["is_deleted", "deleted_at", "content"])
    return message


def edit_message(*, message_id: uuid.UUID, user_id: uuid.UUID, new_content: str) -> Message:
    message = get_message_by_id(message_id)
    if str(message.sender_id) != str(user_id):
        raise MessageDeleteForbiddenError()

    if message.is_deleted:
        from django.core.exceptions import ValidationError

        raise ValidationError("Cannot edit a deleted message.")

    new_content = (new_content or "").strip()
    if not new_content:
        from django.core.exceptions import ValidationError

        raise ValidationError("Message content cannot be empty.")

    from apps.common.moderation.services import moderate_text

    moderate_text(new_content, content_type="message")

    message.content = new_content
    message.is_edited = True
    message.edited_at = timezone.now()
    message.save(update_fields=["content", "is_edited", "edited_at"])
    return message


def mark_conversation_read(*, conversation_id: uuid.UUID, user_id: uuid.UUID) -> int:
    count = ConversationParticipant.objects.filter(
        conversation_id=conversation_id,
        user_id=user_id,
    ).update(last_seen_at=timezone.now())

    if count:
        _invalidate_unread_cache(user_id)

    return count


def add_reaction(*, message_id: uuid.UUID, user_id: uuid.UUID, emoji: str) -> MessageReaction:
    if emoji not in ALLOWED_EMOJI_REACTIONS:
        raise InvalidEmojiError()

    message = get_message_by_id(message_id)
    if not _is_participant(message.conversation_id, user_id):
        raise NotAParticipantError()

    reaction, _ = MessageReaction.objects.get_or_create(
        message_id=message_id,
        user_id=user_id,
        emoji=emoji,
    )
    _dispatch_reaction_event(message.conversation_id, message_id, user_id, emoji, "reaction_added")
    return reaction


def remove_reaction(*, message_id: uuid.UUID, user_id: uuid.UUID, emoji: str) -> None:
    if emoji not in ALLOWED_EMOJI_REACTIONS:
        raise InvalidEmojiError()

    MessageReaction.objects.filter(message_id=message_id, user_id=user_id, emoji=emoji).delete()

    message = get_message_by_id(message_id)
    _dispatch_reaction_event(
        message.conversation_id, message_id, user_id, emoji, "reaction_removed"
    )


def add_participant(
    *,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
    added_by_id: uuid.UUID,
) -> ConversationParticipant:
    conversation = get_conversation_by_id(conversation_id)
    if not conversation.is_group:
        raise GroupConversationRequiredError()

    if not _is_admin(conversation_id, added_by_id):
        raise NotConversationAdminError()

    current_count = ConversationParticipant.objects.filter(conversation_id=conversation_id).count()
    if current_count >= MAX_GROUP_PARTICIPANTS:
        raise MaxParticipantsReachedError()

    participant, created = ConversationParticipant.objects.get_or_create(
        conversation_id=conversation_id,
        user_id=user_id,
        defaults={"role": ParticipantRole.MEMBER},
    )
    if created:
        _send_system_message(conversation, "A new member joined the group.")

    return participant


def remove_participant(
    *,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
    removed_by_id: uuid.UUID,
) -> None:
    conversation = get_conversation_by_id(conversation_id)
    if not conversation.is_group:
        raise GroupConversationRequiredError()

    is_self = str(user_id) == str(removed_by_id)
    is_admin_ = _is_admin(conversation_id, removed_by_id)
    if not is_self and not is_admin_:
        raise NotConversationAdminError()

    ConversationParticipant.objects.filter(conversation_id=conversation_id, user_id=user_id).delete()


def _is_participant(conversation_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    return ConversationParticipant.objects.filter(conversation_id=conversation_id, user_id=user_id).exists()


def _is_admin(conversation_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    return ConversationParticipant.objects.filter(
        conversation_id=conversation_id,
        user_id=user_id,
        role=ParticipantRole.ADMIN,
    ).exists()


def _send_system_message(conversation: Conversation, text: str) -> Message:
    return Message.objects.create(
        conversation=conversation,
        sender=None,
        content=text,
        message_type=MessageType.SYSTEM,
    )


def _dispatch_reaction_event(conversation_id, message_id, user_id, emoji, event_type) -> None:
    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer

        channel_layer = get_channel_layer()
        if channel_layer is None:
            return

        async_to_sync(channel_layer.group_send)(
            get_conversation_group(conversation_id),
            {
                "type": "message_reaction",
                "data": {
                    "type": event_type,
                    "message_id": str(message_id),
                    "user_id": str(user_id),
                    "emoji": emoji,
                    "conversation_id": str(conversation_id),
                },
            },
        )
    except Exception as exc:
        logger.warning("messaging.reaction_dispatch_failed", extra={"error": str(exc)})


def _invalidate_unread_cache(user_id: uuid.UUID) -> None:
    try:
        from apps.messaging.constants import UNREAD_CACHE_KEY
        from core.redis.client import RedisClient

        RedisClient.get_instance().delete(UNREAD_CACHE_KEY.format(user_id=user_id))
    except Exception:
        pass

