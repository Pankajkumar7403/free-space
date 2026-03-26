import uuid

import pytest

from apps.notifications.constants import DevicePlatform
from apps.notifications.models import DeviceToken, Notification, NotificationPreference


@pytest.mark.django_db
class TestNotificationModel:

    def test_uuid_primary_key(self, notification_factory):
        notif = notification_factory()
        assert isinstance(notif.id, uuid.UUID)

    def test_default_is_unread(self, notification_factory):
        notif = notification_factory()
        assert notif.is_read is False

    def test_read_at_null_by_default(self, notification_factory):
        notif = notification_factory()
        assert notif.read_at is None

    def test_str_representation(self, notification_factory):
        notif = notification_factory()
        assert "Notification(" in str(notif)
        assert str(notif.recipient_id) in str(notif)

    def test_timestamps_auto_set(self, notification_factory):
        notif = notification_factory()
        assert notif.created_at is not None
        assert notif.updated_at is not None

    def test_actor_can_be_null(self, notification_factory):
        notif = notification_factory(actor=None)
        assert notif.actor is None

    def test_ordering_newest_first(self, notification_factory, user_factory):
        user = user_factory()
        notification_factory(recipient=user)
        notification_factory(recipient=user)
        results = list(Notification.objects.filter(recipient=user))
        # n2 was created after n1, so it should appear first
        assert results[0].created_at >= results[1].created_at


@pytest.mark.django_db
class TestNotificationPreferenceModel:

    def test_likes_email_default_false(self, user_factory):
        user = user_factory()
        pref, _ = NotificationPreference.objects.get_or_create(user=user)
        assert pref.likes_email is False

    def test_follows_email_default_true(self, user_factory):
        user = user_factory()
        pref, _ = NotificationPreference.objects.get_or_create(user=user)
        assert pref.follows_email is True

    def test_push_defaults_true(self, user_factory):
        user = user_factory()
        pref, _ = NotificationPreference.objects.get_or_create(user=user)
        assert pref.likes_push is True
        assert pref.comments_push is True
        assert pref.follows_push is True

    def test_str_representation(self, user_factory):
        user = user_factory()
        pref, _ = NotificationPreference.objects.get_or_create(user=user)
        assert "NotificationPreference" in str(pref)

    def test_one_preference_per_user(self, user_factory):
        user = user_factory()
        NotificationPreference.objects.get_or_create(user=user)
        NotificationPreference.objects.get_or_create(user=user)  # idempotent
        assert NotificationPreference.objects.filter(user=user).count() == 1


@pytest.mark.django_db
class TestDeviceTokenModel:

    def test_default_active(self, device_token_factory):
        token = device_token_factory()
        assert token.is_active is True

    def test_str_contains_platform(self, device_token_factory):
        token = device_token_factory(platform=DevicePlatform.ANDROID)
        assert "android" in str(token)

    def test_unique_together_user_token(self, user_factory, device_token_factory):
        user = user_factory()
        device_token_factory(user=user, token="unique-abc")
        with pytest.raises(Exception):
            # duplicate (user, token) must fail
            DeviceToken.objects.create(
                user=user, token="unique-abc", platform=DevicePlatform.IOS
            )
