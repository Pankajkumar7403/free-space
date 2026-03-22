# 📁 Location: backend/apps/comments/serializers.py

from rest_framework import serializers
from apps.comments.models import Comment


class CommentSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source="author.username", read_only=True)
    author_avatar   = serializers.SerializerMethodField()
    reply_count     = serializers.IntegerField(read_only=True)
    like_count      = serializers.SerializerMethodField()

    class Meta:
        model  = Comment
        fields = [
            "id", "content", "depth", "is_hidden", "is_pinned", "is_flagged",
            "author_username", "author_avatar",
            "parent", "reply_count", "like_count",
            "created_at", "updated_at",
        ]
        read_only_fields = fields

    def get_author_avatar(self, obj) -> str | None:
        return obj.author.avatar.url if obj.author.avatar else None

    def get_like_count(self, obj) -> int:
        from apps.likes.services import get_like_count
        try:
            return get_like_count(obj=obj)
        except Exception:
            return 0


class CreateCommentSerializer(serializers.Serializer):
    content   = serializers.CharField(max_length=1000)
    parent_id = serializers.UUIDField(required=False, allow_null=True)


class UpdateCommentSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=1000)