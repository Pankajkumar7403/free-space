import uuid
import pytest
from unittest.mock import patch, MagicMock
from django.utils import timezone

from apps.notifications.constants import NotificationType, DevicePlatform
from apps.notifications.exceptions import (
    NotificationNotFoundError,
    UnauthorizedNotificationError,
)
from apps.notifications.models import DeviceToken, Notification
from apps.notifications.services import (
    create_notification,
    delete_notification,
    deregister_device_token,
    mark_all_notifications_read,
    mark_notification_read,
    register_device_token,
    update_notification_preferences,
)


@pytest.mark.django_db
class TestCreateNotification:

    @patch("apps.notifications.dispatchers.dispatch_notification")
    def test_creates_notification_and_dispatches(self, mock_dispatch, user_factory):
        actor     = user_factory()
        recipient = user_factory()

        notif = create_notification(
            recipient_id=recipient.id,
            actor_id=actor.id,
            notification_type=NotificationType.FOLLOW,
        )

        assert notif is not None
        assert notif.recipient_id == recipient.id
        assert notif.actor_id == actor.id
        assert notif.notification_type == NotificationType.FOLLOW
        assert notif.is_read is False
        assert actor.username in notif.message
        mock_dispatch.assert_called_once_with(notif)

    @patch("apps.notifications.dispatchers.dispatch_notification")
    def test_does_not_create_self_notification(self, mock_dispatch, user_factory):
        user = user_factory()
        result = create_notification(
            recipient_id=user.id,
            actor_id=user.id,
            notification_type=NotificationType.LIKE_POST,
        )
        assert result is None
        mock_dispatch.assert_not_called()

    @patch("apps.notifications.dispatchers.dispatch_notification")
    def test_message_template_follow(self, mock_dispatch, user_factory):
        actor     = user_factory()
        recipient = user_factory()
        notif = create_notification(
            recipient_id=recipient.id,
            actor_id=actor.id,
            notification_type=NotificationType.FOLLOW,
        )
        assert "started following you" in notif.message
        assert actor.username in notif.message

    @patch("apps.notifications.dispatchers.dispatch_notification")
    def test_creates_notification_with_target(self, mock_dispatch, user_factory, post_factory):
        actor = user_factory()
        post  = post_factory()
        notif = create_notification(
            recipient_id=post.author_id,
            actor_id=actor.id,
            notification_type=NotificationType.LIKE_POST,
            target_id=post.id,
            target_content_type_label="posts.Post",
        )
        assert notif.object_id == post.id
        assert notif.content_type is not None


@pytest.mark.django_db
class TestMarkNotificationRead:

    def test_marks_read_sets_read_at(self, notification_factory):
        notif = notification_factory(is_read=False)
        updated = mark_notification_read(
            notification_id=notif.id,
            user_id=notif.recipient_id,
        )
        assert updated.is_read is True
        assert updated.read_at is not None

    def test_idempotent_on_already_read(self, notification_factory):
        notif = notification_factory(is_read=True)
        # Should not raise
        mark_notification_read(
            notification_id=notif.id,
            user_id=notif.recipient_id,
        )

    def test_wrong_user_raises_unauthorized(self, notification_factory, user_factory):
        notif = notification_factory()
        other = user_factory()
        with pytest.raises(UnauthorizedNotificationError):
            mark_notification_read(
                notification_id=notif.id,
                user_id=other.id,
            )

    def test_nonexistent_raises_not_found(self):
        with pytest.raises(NotificationNotFoundError):
            mark_notification_read(
                notification_id=uuid.uuid4(),
                user_id=uuid.uuid4(),
            )


@pytest.mark.django_db
class TestMarkAllRead:

    def test_marks_all_unread_for_user(self, notification_factory, user_factory):
        user = user_factory()
        notification_factory(recipient=user, is_read=False)
        notification_factory(recipient=user, is_read=False)
        notification_factory(recipient=user, is_read=True)   # already read

        count = mark_all_notifications_read(user_id=user.id)

        assert count == 2
        assert Notification.objects.filter(recipient=user, is_read=False).count() == 0

    def test_returns_zero_when_all_read(self, user_factory):
        user = user_factory()
        count = mark_all_notifications_read(user_id=user.id)
        assert count == 0


@pytest.mark.django_db
class TestDeleteNotification:

    def test_deletes_notification(self, notification_factory):
        notif = notification_factory()
        notif_id = notif.id
        delete_notification(notification_id=notif_id, user_id=notif.recipient_id)
        assert not Notification.objects.filter(id=notif_id).exists()

    def test_wrong_user_raises(self, notification_factory, user_factory):
        notif = notification_factory()
        other = user_factory()
        with pytest.raises(UnauthorizedNotificationError):
            delete_notification(notification_id=notif.id, user_id=other.id)


@pytest.mark.django_db
class TestDeviceTokenServices:

    def test_register_creates_token(self, user_factory):
        user = user_factory()
        token = register_device_token(
            user_id=user.id,
            token="fcm-register-test",
            platform=DevicePlatform.IOS,
        )
        assert token.user_id == user.id
        assert token.is_active is True

    def test_register_is_idempotent(self, user_factory):
        user = user_factory()
        register_device_token(user_id=user.id, token="idempotent-token", platform=DevicePlatform.IOS)
        register_device_token(user_id=user.id, token="idempotent-token", platform=DevicePlatform.IOS)
        assert DeviceToken.objects.filter(user=user, token="idempotent-token").count() == 1

    def test_deregister_sets_inactive(self, user_factory, device_token_factory):
        user  = user_factory()
        token = device_token_factory(user=user, token="deregister-me")
        deregister_device_token(user_id=user.id, token="deregister-me")
        token.refresh_from_db()
        assert token.is_active is False


@pytest.mark.django_db
class TestUpdatePreferences:

    def test_updates_preference_fields(self, user_factory):
        user = user_factory()
        prefs = update_notification_preferences(
            user_id=user.id,
            preferences={"likes_email": True, "follows_push": False},
        )
        assert prefs.likes_email is True
        assert prefs.follows_push is False

    def test_ignores_unknown_fields(self, user_factory):
        user = user_factory()
        # Should not raise
        update_notification_preferences(
            user_id=user.id,
            preferences={"unknown_field": True},
        )