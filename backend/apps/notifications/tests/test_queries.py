import uuid

import pytest

from apps.notifications.exceptions import NotificationNotFoundError
from apps.notifications.selectors import (
    get_active_device_tokens,
    get_notification_by_id,
    get_notifications_for_user,
    get_unread_notification_count,
)


@pytest.mark.django_db
class TestGetNotificationById:

    def test_returns_correct_notification(self, notification_factory):
        notif = notification_factory()
        result = get_notification_by_id(notif.id)
        assert result.id == notif.id

    def test_raises_not_found_for_unknown_id(self):
        with pytest.raises(NotificationNotFoundError):
            get_notification_by_id(uuid.uuid4())


@pytest.mark.django_db
class TestGetNotificationsForUser:

    def test_returns_only_user_notifications(self, notification_factory, user_factory):
        user = user_factory()
        other = user_factory()
        notification_factory(recipient=user)
        notification_factory(recipient=user)
        notification_factory(recipient=other)

        results = get_notifications_for_user(user.id)
        assert results.count() == 2

    def test_unread_only_flag(self, notification_factory, user_factory):
        user = user_factory()
        notification_factory(recipient=user, is_read=False)
        notification_factory(recipient=user, is_read=True)

        unread_only = get_notifications_for_user(user.id, include_read=False)
        assert unread_only.count() == 1
        assert all(not n.is_read for n in unread_only)

    def test_ordered_newest_first(self, notification_factory, user_factory):
        user = user_factory()
        notification_factory(recipient=user)
        notification_factory(recipient=user)

        results = list(get_notifications_for_user(user.id))
        assert results[0].created_at >= results[-1].created_at


@pytest.mark.django_db
class TestGetUnreadNotificationCount:

    def test_correct_unread_count(self, notification_factory, user_factory):
        user = user_factory()
        notification_factory(recipient=user, is_read=False)
        notification_factory(recipient=user, is_read=False)
        notification_factory(recipient=user, is_read=True)

        count = get_unread_notification_count(user.id)
        assert count == 2

    def test_returns_zero_for_no_notifications(self, user_factory):
        user = user_factory()
        assert get_unread_notification_count(user.id) == 0


@pytest.mark.django_db
class TestGetActiveDeviceTokens:

    def test_returns_only_active_tokens(self, user_factory, device_token_factory):
        user = user_factory()
        device_token_factory(user=user, is_active=True)
        device_token_factory(user=user, is_active=False)

        active = get_active_device_tokens(user.id)
        assert active.count() == 1
        assert all(t.is_active for t in active)
