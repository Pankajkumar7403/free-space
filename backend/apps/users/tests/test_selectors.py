# 📁 Location: backend/apps/users/tests/test_selectors.py
# ▶  Run:      pytest apps/users/tests/test_selectors.py -v

import pytest
from apps.users.exceptions import UserNotFoundError
from apps.users.models import BlockedUser, Follow, MutedUser
from apps.users.selectors import (
    email_exists, get_blocked_users, get_follower_count,
    get_followers, get_following, get_following_count,
    get_muted_users, get_user_by_email, get_user_by_id,
    get_user_by_username, is_blocked, is_following, is_muted,
    search_users, username_exists,
)
from apps.users.tests.factories import UserFactory

pytestmark = [pytest.mark.unit, pytest.mark.django_db]


class TestGetUserById:
    def test_returns_user(self, user):
        result = get_user_by_id(user.pk)
        assert result.pk == user.pk

    def test_raises_for_missing_id(self):
        import uuid
        with pytest.raises(UserNotFoundError):
            get_user_by_id(uuid.uuid4())

    def test_raises_for_inactive_user(self, inactive_user):
        with pytest.raises(UserNotFoundError):
            get_user_by_id(inactive_user.pk)


class TestGetUserByEmail:
    def test_returns_user(self, user):
        result = get_user_by_email(user.email)
        assert result.pk == user.pk

    def test_case_insensitive(self, user):
        result = get_user_by_email(user.email.upper())
        assert result.pk == user.pk

    def test_raises_when_not_found(self):
        with pytest.raises(UserNotFoundError):
            get_user_by_email("nobody@example.com")


class TestFollowSelectors:
    def test_get_followers(self, db):
        a = UserFactory()
        b = UserFactory()
        Follow.objects.create(follower=b, following=a, status="accepted")
        followers = list(get_followers(a))
        assert b in followers

    def test_get_following(self, db):
        a = UserFactory()
        b = UserFactory()
        Follow.objects.create(follower=a, following=b, status="accepted")
        following = list(get_following(a))
        assert b in following

    def test_follower_count(self, db):
        a = UserFactory()
        for _ in range(3):
            follower = UserFactory()
            Follow.objects.create(follower=follower, following=a, status="accepted")
        assert get_follower_count(a) == 3

    def test_is_following_true(self, db):
        a = UserFactory()
        b = UserFactory()
        Follow.objects.create(follower=a, following=b, status="accepted")
        assert is_following(a, b) is True

    def test_is_following_false(self, db):
        a = UserFactory()
        b = UserFactory()
        assert is_following(a, b) is False

    def test_pending_not_counted_as_following(self, db):
        a = UserFactory()
        b = UserFactory()
        Follow.objects.create(follower=a, following=b, status="pending")
        assert is_following(a, b) is False


class TestBlockMuteSelectors:
    def test_is_blocked_true(self, db):
        a = UserFactory()
        b = UserFactory()
        BlockedUser.objects.create(blocker=a, blocked=b)
        assert is_blocked(a, b) is True

    def test_is_blocked_false(self, db):
        a = UserFactory()
        b = UserFactory()
        assert is_blocked(a, b) is False

    def test_is_muted(self, db):
        a = UserFactory()
        b = UserFactory()
        MutedUser.objects.create(muter=a, muted=b)
        assert is_muted(a, b) is True


class TestSearchUsers:
    def test_finds_by_username(self, db):
        u = UserFactory(username="rainbow_user", public=True)
        results = list(search_users("rainbow"))
        assert u in results

    def test_excludes_private_users(self, db):
        private = UserFactory(username="secret_user", private=True)
        results = list(search_users("secret"))
        assert private not in results

    def test_excludes_self(self, db):
        u = UserFactory(username="selftest_user", public=True)
        results = list(search_users("selftest", exclude_user=u))
        assert u not in results