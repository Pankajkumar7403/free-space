# 📁 Location: backend/apps/users/tests/test_services.py
# ▶  Run:      pytest apps/users/tests/test_services.py -v

from unittest.mock import patch

import pytest

from apps.users.services import accept_follow_request, follow_user

pytestmark = [pytest.mark.django_db]


def test_follow_public_user_fires_notification(user_factory):
    """Following a public user (auto-accepted) creates a follow notification."""
    follower = user_factory()
    following = user_factory()  # public by default

    with patch("apps.notifications.services.create_notification") as mock_notify:
        follow_user(follower_id=follower.pk, following_id=following.pk)
        mock_notify.assert_called_once()
        assert mock_notify.call_args.kwargs["recipient_id"] == following.pk
        assert mock_notify.call_args.kwargs["actor_id"] == follower.pk


def test_follow_private_user_no_notification(user_factory):
    """Following a private user (pending status) does NOT fire a notification."""
    from apps.users.constants import AccountPrivacyChoices

    follower = user_factory()
    following = user_factory()
    following.account_privacy = AccountPrivacyChoices.PRIVATE
    following.save(update_fields=["account_privacy"])

    with patch("apps.notifications.services.create_notification") as mock_notify:
        follow_user(follower_id=follower.pk, following_id=following.pk)
        mock_notify.assert_not_called()


def test_accept_follow_request_fires_notification(user_factory):
    """Accepting a pending follow request fires a follow notification."""
    from apps.users.constants import AccountPrivacyChoices

    follower = user_factory()
    following = user_factory()
    following.account_privacy = AccountPrivacyChoices.PRIVATE
    following.save(update_fields=["account_privacy"])
    follow_user(follower_id=follower.pk, following_id=following.pk)

    with patch("apps.notifications.services.create_notification") as mock_notify:
        accept_follow_request(user_id=following.pk, follower_id=follower.pk)
        mock_notify.assert_called_once()
        assert mock_notify.call_args.kwargs["recipient_id"] == following.pk
        assert mock_notify.call_args.kwargs["actor_id"] == follower.pk


def test_refollow_does_not_double_notify(user_factory):
    """Re-following after unfollow fires exactly one notification (not two)."""
    from apps.users.services import unfollow_user

    follower = user_factory()
    following = user_factory()
    follow_user(follower_id=follower.pk, following_id=following.pk)
    unfollow_user(follower_id=follower.pk, following_id=following.pk)

    with patch("apps.notifications.services.create_notification") as mock_notify:
        follow_user(follower_id=follower.pk, following_id=following.pk)
        mock_notify.assert_called_once()
