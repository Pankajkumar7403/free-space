# 📁 Location: backend/apps/likes/serializers.py

from rest_framework import serializers

from apps.likes.models import Like


class LikeSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Like
        fields = ["id", "username", "object_id", "created_at"]
        read_only_fields = fields


class LikeCountSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    liked_by_me = serializers.BooleanField()
