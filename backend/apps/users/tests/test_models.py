"""
Test model behaviour — constraints, properties, methods.
These never go through views or services.
"""
import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from apps.users.tests.factories import UserFactory

User = get_user_model()

pytestmark = [pytest.mark.unit, pytest.mark.django_db]


class TestUserModel:
    def test_str_representation(self, user):
        # Adjust if your User.__str__ differs
        assert str(user) == user.email or str(user) == user.username

    def test_email_is_unique(self, user):
        with pytest.raises(IntegrityError):
            UserFactory(email=user.email)

    def test_username_is_unique(self, user):
        with pytest.raises(IntegrityError):
            UserFactory(username=user.username)

    def test_password_is_hashed(self, db):
        user = UserFactory()
        assert not user.password.startswith("testpass")
        assert user.check_password("testpass123")

    def test_inactive_by_trait(self, inactive_user):
        assert inactive_user.is_active is False

    def test_staff_by_trait(self, staff_user):
        assert staff_user.is_staff is True