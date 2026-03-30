from __future__ import annotations

from rest_framework import serializers

from apps.messaging.constants import (
    ALLOWED_EMOJI_REACTIONS,
    MAX_GROUP_NAME_LENGTH,
    MAX_MESSAGE_LENGTH,
    PRESENCE_KEY,
)
from apps.messaging.models import Conversation, ConversationParticipant, Message


class MessageSerializer(serializers.ModelSerializer):
    sender_id = serializers.UUIDField(allow_null=True, read_only=True)
    sender_username = serializers.CharField(
        source="sender.username", read_only=True, allow_null=True
    )
    sender_avatar = serializers.SerializerMethodField()
    display_content = serializers.SerializerMethodField()
    reply_to_id = serializers.UUIDField(allow_null=True, read_only=True)
    reply_preview = serializers.SerializerMethodField()
    reactions = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            "id",
            "conversation_id",
            "sender_id",
            "sender_username",
            "sender_avatar",
            "content",
            "display_content",
            "message_type",
            "is_deleted",
            "is_edited",
            "reply_to_id",
            "reply_preview",
            "reactions",
            "created_at",
            "edited_at",
        ]
        read_only_fields = fields

    def get_sender_avatar(self, obj) -> str | None:
        if not obj.sender or not getattr(obj.sender, "avatar", None):
            return None
        try:
            return obj.sender.avatar.url
        except Exception:
            return None

    def get_display_content(self, obj) -> str:
        return obj.get_display_content()

    def get_reply_preview(self, obj) -> dict | None:
        if not obj.reply_to:
            return None
        return {
            "id": str(obj.reply_to.id),
            "content": obj.reply_to.get_display_content()[:80],
            "sender": getattr(obj.reply_to.sender, "username", None),
        }

    def get_reactions(self, obj) -> dict:
        from apps.messaging.selectors import get_message_reactions_summary

        return get_message_reactions_summary(obj.id)


class ParticipantSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    avatar_url = serializers.SerializerMethodField()
    is_online = serializers.SerializerMethodField()

    class Meta:
        model = ConversationParticipant
        fields = [
            "user_id",
            "username",
            "avatar_url",
            "role",
            "joined_at",
            "is_muted",
            "is_archived",
            "is_online",
        ]
        read_only_fields = fields

    def get_avatar_url(self, obj) -> str | None:
        if not getattr(obj.user, "avatar", None):
            return None
        try:
            return obj.user.avatar.url
        except Exception:
            return None

    def get_is_online(self, obj) -> bool:
        try:
            from core.redis.client import RedisClient

            redis = RedisClient.get_instance()
            return bool(redis.get(PRESENCE_KEY.format(user_id=obj.user_id)))
        except Exception:
            return False


class ConversationSerializer(serializers.ModelSerializer):
    participants = ParticipantSerializer(many=True, read_only=True)
    unread_count = serializers.SerializerMethodField()
    other_participant = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            "id",
            "conversation_type",
            "name",
            "last_message_preview",
            "last_message_at",
            "participants",
            "unread_count",
            "other_participant",
            "created_at",
        ]
        read_only_fields = fields

    def get_unread_count(self, obj) -> int:
        request = self.context.get("request")
        if not request:
            return 0
        from apps.messaging.selectors import get_unread_count_per_conversation

        return get_unread_count_per_conversation(request.user.id, obj.id)

    def get_other_participant(self, obj) -> dict | None:
        if not obj.is_direct:
            return None

        request = self.context.get("request")
        if not request:
            return None

        other = next(
            (
                p
                for p in obj.participants.all()
                if str(p.user_id) != str(request.user.id)
            ),
            None,
        )
        if not other:
            return None
        avatar_url = None
        avatar_field = getattr(other.user, "avatar", None)
        if avatar_field:
            try:
                avatar_url = avatar_field.url
            except Exception:
                avatar_url = None
        return {
            "user_id": str(other.user_id),
            "username": getattr(other.user, "username", ""),
            "avatar": avatar_url,
        }


class CreateDirectConversationSerializer(serializers.Serializer):
    target_user_id = serializers.UUIDField()


class CreateGroupConversationSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=MAX_GROUP_NAME_LENGTH)
    participant_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=2,
        max_length=99,
    )


class SendMessageSerializer(serializers.Serializer):
    content = serializers.CharField(
        max_length=MAX_MESSAGE_LENGTH, required=False, allow_blank=True
    )
    media_id = serializers.UUIDField(required=False, allow_null=True)
    reply_to_id = serializers.UUIDField(required=False, allow_null=True)

    def validate(self, data):
        if not data.get("content") and not data.get("media_id"):
            raise serializers.ValidationError("Either content or media_id is required.")
        return data


class EditMessageSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=MAX_MESSAGE_LENGTH)


class AddReactionSerializer(serializers.Serializer):
    emoji = serializers.ChoiceField(choices=sorted(ALLOWED_EMOJI_REACTIONS))


class AddParticipantSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
