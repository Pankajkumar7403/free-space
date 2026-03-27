# 📁 Location: backend/apps/users/tests/test_views.py
# ▶  Run:      pytest apps/users/tests/test_views.py -v

import pytest

from apps.users.tests.factories import UserFactory
from core.testing.base import BaseAPITestCase

pytestmark = [pytest.mark.e2e, pytest.mark.django_db]


class TestRegisterView(BaseAPITestCase):
    url = "/api/v1/users/register/"

    def test_register_success(self):
        res = self.client.post(
            self.url,
            {
                "email": "new@example.com",
                "username": "newuser",
                "password": "securepass123",
            },
        )
        self.assert_created(res)
        assert res.data["user"]["email"] == "new@example.com"
        assert "access" in res.data
        assert "refresh" in res.data

    def test_register_duplicate_email(self):
        UserFactory(email="dup@example.com")
        res = self.client.post(
            self.url,
            {"email": "dup@example.com", "username": "other99", "password": "pass1234"},
        )
        self.assert_status(res, 409)
        self.assert_error_code(res, "EMAIL_TAKEN")

    def test_register_missing_fields(self):
        res = self.client.post(self.url, {"email": "only@example.com"})
        self.assert_bad_request(res)

    def test_register_invalid_email(self):
        res = self.client.post(
            self.url,
            {"email": "not-valid", "username": "someone", "password": "pass1234"},
        )
        self.assert_bad_request(res)


class TestLoginView(BaseAPITestCase):
    url = "/api/v1/users/login/"

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.user.set_password("mypassword")
        self.user.save()

    def test_login_success(self):
        res = self.client.post(
            self.url, {"email": self.user.email, "password": "mypassword"}
        )
        self.assert_ok(res)
        assert "access" in res.data
        assert "refresh" in res.data

    def test_login_wrong_password(self):
        res = self.client.post(
            self.url, {"email": self.user.email, "password": "wrong"}
        )
        self.assert_unauthorized(res)
        self.assert_error_code(res, "INVALID_CREDENTIALS")

    def test_login_unknown_email(self):
        res = self.client.post(self.url, {"email": "ghost@x.com", "password": "pass"})
        self.assert_unauthorized(res)


class TestMeView(BaseAPITestCase):
    url = "/api/v1/users/me/"

    def test_returns_own_profile(self, user=None):
        user = UserFactory()
        self.authenticate(user)
        res = self.client.get(self.url)
        self.assert_ok(res)
        assert res.data["email"] == user.email

    def test_unauthenticated_returns_401(self):
        res = self.client.get(self.url)
        self.assert_unauthorized(res)


class TestUserDetailView(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.authenticate(self.user)

    def test_get_own_profile_returns_private_data(self):
        res = self.client.get(f"/api/v1/users/{self.user.pk}/")
        self.assert_ok(res)
        assert "email" in res.data  # private field visible on own profile

    def test_get_other_profile_returns_public_data(self):
        other = UserFactory(public=True)
        res = self.client.get(f"/api/v1/users/{other.pk}/")
        self.assert_ok(res)
        assert "email" not in res.data  # private field hidden

    def test_update_own_profile(self):
        res = self.client.patch(
            f"/api/v1/users/{self.user.pk}/",
            {"display_name": "Rainbow"},
        )
        self.assert_ok(res)
        assert res.data["display_name"] == "Rainbow"

    def test_update_other_profile_is_forbidden(self):
        other = UserFactory()
        res = self.client.patch(f"/api/v1/users/{other.pk}/", {"display_name": "Hack"})
        self.assert_forbidden(res)

    def test_404_on_nonexistent_user(self):
        import uuid

        res = self.client.get(f"/api/v1/users/{uuid.uuid4()}/")
        self.assert_not_found(res)
        self.assert_error_code(res, "USER_NOT_FOUND")

    def test_deactivate_own_account(self):
        res = self.client.delete(f"/api/v1/users/{self.user.pk}/")
        self.assert_no_content(res)
        self.user.refresh_from_db()
        assert self.user.is_active is False


class TestFollowViews(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory(public=True)
        self.authenticate(self.user)

    def test_follow_user(self):
        other = UserFactory(public=True)
        res = self.client.post(f"/api/v1/users/{other.pk}/follow/")
        self.assert_created(res)
        assert res.data["status"] == "accepted"

    def test_follow_private_user_is_pending(self):
        other = UserFactory(private=True)
        res = self.client.post(f"/api/v1/users/{other.pk}/follow/")
        self.assert_created(res)
        assert res.data["status"] == "pending"

    def test_cannot_follow_self(self):
        res = self.client.post(f"/api/v1/users/{self.user.pk}/follow/")
        self.assert_bad_request(res)
        self.assert_error_code(res, "CANNOT_FOLLOW_SELF")
