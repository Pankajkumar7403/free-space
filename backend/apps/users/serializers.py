# 📁 Location: backend/apps/users/serializers.py

from __future__ import annotations

from rest_framework import serializers

from apps.users.models import Follow, User
from apps.users.validators import validate_password_strength, validate_username

# ── Output serializers (read) ──────────────────────────────────────────────────


class UserPublicSerializer(serializers.ModelSerializer):
    """
    Public profile — safe to return to ANY authenticated user.
    Sensitive identity fields are EXCLUDED; use UserPrivateSerializer for own profile.
    """

    follower_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "display_name",
            "bio",
            "avatar",
            "account_privacy",
            "is_verified",
            "date_joined",
            "follower_count",
            "following_count",
            # pronouns visible if visibility=public
            "pronouns",
        ]
        read_only_fields = fields

    def get_follower_count(self, obj) -> int:
        return Follow.objects.filter(following=obj, status="accepted").count()

    def get_following_count(self, obj) -> int:
        return Follow.objects.filter(follower=obj, status="accepted").count()


class UserPrivateSerializer(serializers.ModelSerializer):
    """
    Own profile — full data including identity fields and privacy settings.
    Only returned to the authenticated user themselves.
    """

    follower_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "display_name",
            "first_name",
            "last_name",
            "bio",
            "website",
            "avatar",
            "pronouns",
            "pronouns_custom",
            "pronouns_visibility",
            "gender_identity",
            "gender_identity_custom",
            "gender_identity_visibility",
            "sexual_orientation",
            "sexual_orientation_custom",
            "sexual_orientation_visibility",
            "account_privacy",
            "safe_messaging_mode",
            "location_sharing",
            "is_verified",
            "date_joined",
            "last_seen",
            "follower_count",
            "following_count",
        ]
        read_only_fields = fields

    def get_follower_count(self, obj) -> int:
        return Follow.objects.filter(following=obj, status="accepted").count()

    def get_following_count(self, obj) -> int:
        return Follow.objects.filter(follower=obj, status="accepted").count()


# ── Input serializers (write) ──────────────────────────────────────────────────


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField(max_length=30)
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_username(self, value: str) -> str:
        validate_username(value)
        return value

    def validate_password(self, value: str) -> str:
        validate_password_strength(value)
        return value


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=512)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_new_password(self, value: str) -> str:
        validate_password_strength(value)
        return value


class VerifyEmailSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=512)
    email = serializers.EmailField(required=False)


class ResendVerificationEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)


class OAuthInitSerializer(serializers.Serializer):
    redirect_uri = serializers.URLField()


class OAuthCallbackSerializer(serializers.Serializer):
    code = serializers.CharField()
    redirect_uri = serializers.URLField()
    state = serializers.CharField(required=False, allow_blank=True)


class TokenResponseSerializer(serializers.Serializer):
    """Shape of the JWT token pair response."""

    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)
    user = UserPrivateSerializer(read_only=True)


class UpdateProfileSerializer(serializers.Serializer):
    display_name = serializers.CharField(
        max_length=60, required=False, allow_blank=True
    )
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    username = serializers.CharField(max_length=30, required=False)
    bio = serializers.CharField(max_length=500, required=False, allow_blank=True)
    website = serializers.URLField(required=False, allow_blank=True)

    # Identity fields
    pronouns = serializers.CharField(max_length=20, required=False, allow_blank=True)
    pronouns_custom = serializers.CharField(
        max_length=50, required=False, allow_blank=True
    )
    pronouns_visibility = serializers.CharField(max_length=10, required=False)
    gender_identity = serializers.CharField(
        max_length=20, required=False, allow_blank=True
    )
    gender_identity_custom = serializers.CharField(
        max_length=100, required=False, allow_blank=True
    )
    gender_identity_visibility = serializers.CharField(max_length=10, required=False)
    sexual_orientation = serializers.CharField(
        max_length=20, required=False, allow_blank=True
    )
    sexual_orientation_custom = serializers.CharField(
        max_length=100, required=False, allow_blank=True
    )
    sexual_orientation_visibility = serializers.CharField(max_length=10, required=False)

    # Privacy
    account_privacy = serializers.CharField(max_length=15, required=False)
    safe_messaging_mode = serializers.BooleanField(required=False)

    def validate_username(self, value: str) -> str:
        validate_username(value)
        return value


class RefreshTokenSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class FollowSerializer(serializers.ModelSerializer):
    follower_username = serializers.CharField(
        source="follower.username", read_only=True
    )
    following_username = serializers.CharField(
        source="following.username", read_only=True
    )

    class Meta:
        model = Follow
        fields = [
            "id",
            "follower_username",
            "following_username",
            "status",
            "created_at",
        ]
        read_only_fields = fields
