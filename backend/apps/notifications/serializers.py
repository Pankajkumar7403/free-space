from __future__ import annotations

from rest_framework import serializers

from apps.notifications.constants import DevicePlatform
from apps.notifications.models import Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    actor_id = serializers.UUIDField(allow_null=True, read_only=True)
    actor_username = serializers.CharField(
        source="actor.username", read_only=True, allow_null=True
    )
    actor_avatar = serializers.SerializerMethodField()
    target_id = serializers.UUIDField(
        source="object_id", read_only=True, allow_null=True
    )

    class Meta:
        model = Notification
        fields = [
            "id",
            "notification_type",
            "actor_id",
            "actor_username",
            "actor_avatar",
            "message",
            "is_read",
            "read_at",
            "target_id",
            "created_at",
        ]
        read_only_fields = fields

    def get_actor_avatar(self, obj) -> str | None:
        if obj.actor:
            return getattr(obj.actor, "avatar_url", None)
        return None


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        exclude = ["id", "user", "created_at", "updated_at", "deleted_at"]


class NotificationPreferenceUpdateSerializer(serializers.Serializer):
    likes_in_app = serializers.BooleanField(required=False)
    likes_push = serializers.BooleanField(required=False)
    likes_email = serializers.BooleanField(required=False)
    comments_in_app = serializers.BooleanField(required=False)
    comments_push = serializers.BooleanField(required=False)
    comments_email = serializers.BooleanField(required=False)
    follows_in_app = serializers.BooleanField(required=False)
    follows_push = serializers.BooleanField(required=False)
    follows_email = serializers.BooleanField(required=False)
    mentions_in_app = serializers.BooleanField(required=False)
    mentions_push = serializers.BooleanField(required=False)
    mentions_email = serializers.BooleanField(required=False)


class DeviceTokenRegisterSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=512)
    platform = serializers.ChoiceField(choices=DevicePlatform.choices)


class DeviceTokenDeregisterSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=512)
