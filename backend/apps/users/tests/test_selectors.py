# 📁 Location: backend/apps/users/tests/test_selectors.py
# ▶  Run:      pytest apps/users/tests/test_selectors.py -v
"""
Test selectors (read queries).

These are unit tests — they hit the DB but do no HTTP.
Mark: unit + django_db
"""
import pytest

from apps.users.exceptions import UserNotFoundError
from apps.users.selectors import (
    email_exists,
    get_active_users,
    get_user_by_email,
    get_user_by_id,
    get_user_by_username,
    username_exists,
)
from apps.users.tests.factories import UserFactory

pytestmark = [pytest.mark.unit, pytest.mark.django_db]


class TestGetUserById:
    def test_returns_user_when_exists(self, user):
        result = get_user_by_id(user.pk)
        assert result.pk == user.pk

    def test_raises_when_not_found(self):
        with pytest.raises(UserNotFoundError):
            get_user_by_id(99999)

    def test_raises_when_inactive(self, inactive_user):
        with pytest.raises(UserNotFoundError):
            get_user_by_id(inactive_user.pk)


class TestGetUserByEmail:
    def test_returns_user_case_insensitive(self, user):
        result = get_user_by_email(user.email.upper())
        assert result.pk == user.pk

    def test_raises_when_not_found(self):
        with pytest.raises(UserNotFoundError):
            get_user_by_email("ghost@example.com")


class TestGetUserByUsername:
    def test_returns_user(self, user):
        result = get_user_by_username(user.username)
        assert result.pk == user.pk

    def test_case_insensitive(self, user):
        result = get_user_by_username(user.username.upper())
        assert result.pk == user.pk

    def test_raises_when_not_found(self):
        with pytest.raises(UserNotFoundError):
            get_user_by_username("nobody")


class TestGetActiveUsers:
    def test_excludes_inactive_users(self, user, inactive_user):
        qs = get_active_users()
        pks = list(qs.values_list("pk", flat=True))
        assert user.pk in pks
        assert inactive_user.pk not in pks

    def test_ordered_newest_first(self, db):
        u1 = UserFactory()
        u2 = UserFactory()
        qs = list(get_active_users())
        # u2 joined after u1
        assert qs.index(u2) < qs.index(u1)


class TestExistenceChecks:
    def test_email_exists_true(self, user):
        assert email_exists(user.email) is True

    def test_email_exists_false(self):
        assert email_exists("nobody@example.com") is False

    def test_username_exists_true(self, user):
        assert username_exists(user.username) is True

    def test_username_exists_false(self):
        assert username_exists("nobodyatall") is False