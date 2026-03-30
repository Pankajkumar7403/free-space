from __future__ import annotations

import uuid
from typing import Optional

from django.db.models import Count, QuerySet

from apps.messaging.constants import UNREAD_CACHE_KEY, UNREAD_CACHE_TTL
from apps.messaging.exceptions import ConversationNotFoundError, MessageNotFoundError
from apps.messaging.models import (
    Conversation,
    ConversationParticipant,
    Message,
    MessageReaction,
)


def get_conversation_by_id(conversation_id: uuid.UUID) -> Conversation:
    try:
        return Conversation.objects.get(id=conversation_id)
    except Conversation.DoesNotExist:
        raise ConversationNotFoundError(conversation_id)


def get_message_by_id(message_id: uuid.UUID) -> Message:
    try:
        return Message.objects.select_related("sender", "conversation").get(
            id=message_id
        )
    except Message.DoesNotExist:
        raise MessageNotFoundError(message_id)


def get_user_conversations(user_id: uuid.UUID) -> QuerySet[Conversation]:
    return (
        Conversation.objects.filter(
            participants__user_id=user_id,
            participants__is_archived=False,
        )
        .select_related("last_message_sender")
        .prefetch_related("participants__user")
        .order_by("-last_message_at")
    )


def get_conversation_messages(
    conversation_id: uuid.UUID,
    *,
    before_id: Optional[uuid.UUID] = None,
) -> QuerySet[Message]:
    qs = (
        Message.objects.filter(conversation_id=conversation_id)
        .select_related("sender", "reply_to__sender")
        .prefetch_related("reactions")
        .order_by("-created_at")
    )
    if before_id:
        try:
            pivot = Message.objects.get(id=before_id)
            qs = qs.filter(created_at__lt=pivot.created_at)
        except Message.DoesNotExist:
            pass
    return qs


def get_unread_message_count(user_id: uuid.UUID) -> int:
    try:
        from core.redis.client import RedisClient

        redis = RedisClient.get_instance()
        cache_key = UNREAD_CACHE_KEY.format(user_id=user_id)
        cached = redis.get(cache_key)
        if cached is not None:
            try:
                return int(cached)
            except Exception:
                return int(cached.decode())  # pragma: no cover
    except Exception:
        pass

    count = _compute_unread_count(user_id)

    try:
        redis.setex(cache_key, UNREAD_CACHE_TTL, count)
    except Exception:
        pass

    return count


def get_unread_count_per_conversation(
    user_id: uuid.UUID, conversation_id: uuid.UUID
) -> int:
    try:
        participant = ConversationParticipant.objects.get(
            conversation_id=conversation_id,
            user_id=user_id,
        )
    except ConversationParticipant.DoesNotExist:
        return 0

    qs = Message.objects.filter(conversation_id=conversation_id).exclude(
        sender_id=user_id
    )
    qs = qs.exclude(message_type="system")
    if participant.last_seen_at:
        qs = qs.filter(created_at__gt=participant.last_seen_at)
    return qs.count()


def get_participant(
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Optional[ConversationParticipant]:
    try:
        return ConversationParticipant.objects.get(
            conversation_id=conversation_id,
            user_id=user_id,
        )
    except ConversationParticipant.DoesNotExist:
        return None


def get_message_reactions_summary(message_id: uuid.UUID) -> dict:
    reactions = (
        MessageReaction.objects.filter(message_id=message_id)
        .values("emoji")
        .annotate(count=Count("id"))
    )
    return {r["emoji"]: r["count"] for r in reactions}


def _compute_unread_count(user_id: uuid.UUID) -> int:
    participants = ConversationParticipant.objects.filter(user_id=user_id)
    total = 0
    for p in participants:
        qs = (
            Message.objects.filter(conversation_id=p.conversation_id)
            .exclude(sender_id=user_id)
            .exclude(message_type="system")
        )
        if p.last_seen_at:
            qs = qs.filter(created_at__gt=p.last_seen_at)
        total += qs.count()
    return total
