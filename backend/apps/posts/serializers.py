# 📁 Location: backend/apps/posts/serializers.py

from rest_framework import serializers

from apps.posts.constants import PostVisibility
from apps.posts.models import Hashtag, Media, Post


class HashtagSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Hashtag
        fields = ["id", "name"]
        read_only_fields = fields


class MediaSerializer(serializers.ModelSerializer):
    display_url = serializers.CharField(read_only=True)

    class Meta:
        model  = Media
        fields = [
            "id", "media_type", "status",
            "original_url", "processed_url", "thumbnail_url", "display_url",
            "width", "height", "duration", "alt_text", "created_at",
        ]
        read_only_fields = fields


class PostSerializer(serializers.ModelSerializer):
    """Full post — returned on detail and create."""
    author_username = serializers.CharField(source="author.username", read_only=True)
    author_avatar   = serializers.SerializerMethodField()
    hashtags        = HashtagSerializer(many=True, read_only=True)
    media           = MediaSerializer(many=True, read_only=True)

    class Meta:
        model  = Post
        fields = [
            "id", "content", "visibility", "allow_comments", "is_anonymous",
            "status", "location_name", "latitude", "longitude",
            "author_username", "author_avatar",
            "hashtags", "media",
            "created_at", "updated_at",
        ]
        read_only_fields = fields

    def get_author_avatar(self, obj) -> str | None:
        if obj.is_anonymous:
            return None
        return obj.author.avatar.url if obj.author.avatar else None


class PostListSerializer(serializers.ModelSerializer):
    """Lighter serializer used in list/feed views."""
    author_username = serializers.CharField(source="author.username", read_only=True)
    thumbnail_url   = serializers.SerializerMethodField()

    class Meta:
        model  = Post
        fields = [
            "id", "content", "visibility", "is_anonymous",
            "author_username", "thumbnail_url",
            "created_at",
        ]
        read_only_fields = fields

    def get_thumbnail_url(self, obj) -> str | None:
        first = obj.media.first()
        return first.thumbnail_url if first else None


class CreatePostSerializer(serializers.Serializer):
    content        = serializers.CharField(max_length=2200)
    visibility     = serializers.ChoiceField(
        choices=PostVisibility.choices,
        default=PostVisibility.FOLLOWERS_ONLY,
    )
    allow_comments = serializers.BooleanField(default=True)
    is_anonymous   = serializers.BooleanField(default=False)
    location_name  = serializers.CharField(max_length=200, required=False, allow_blank=True)
    latitude       = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    longitude      = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    media_ids      = serializers.ListField(
        child=serializers.UUIDField(), required=False, default=list, max_length=10
    )


class UpdatePostSerializer(serializers.Serializer):
    content        = serializers.CharField(max_length=2200, required=False)
    visibility     = serializers.ChoiceField(choices=PostVisibility.choices, required=False)
    allow_comments = serializers.BooleanField(required=False)
    location_name  = serializers.CharField(max_length=200, required=False, allow_blank=True)


class PresignedUrlRequestSerializer(serializers.Serializer):
    """Input for requesting a presigned S3 upload URL."""
    mime_type  = serializers.CharField(max_length=100)
    file_size  = serializers.IntegerField(min_value=1)
    alt_text   = serializers.CharField(max_length=500, required=False, allow_blank=True)


class PresignedUrlResponseSerializer(serializers.Serializer):
    """Response shape for presigned URL endpoint."""
    media_id     = serializers.UUIDField(read_only=True)
    upload_url   = serializers.URLField(read_only=True)
    expires_in   = serializers.IntegerField(read_only=True)
    media_type   = serializers.CharField(read_only=True)