# 📁 Location: backend/apps/users/tests/test_models.py
# ▶  Run:      pytest apps/users/tests/test_models.py -v

import uuid
import pytest
from django.db import IntegrityError
from apps.users.models import BlockedUser, Follow, MutedUser, User
from apps.users.tests.factories import UserFactory

pytestmark = [pytest.mark.unit, pytest.mark.django_db]


class TestUserModel:
    def test_pk_is_uuid(self, user):
        assert isinstance(user.pk, uuid.UUID)

    def test_str_is_email(self, user):
        assert str(user) == user.email

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

    def test_default_privacy_is_followers_only(self, db):
        user = UserFactory()
        assert user.account_privacy == "followers_only"

    def test_default_safe_messaging_is_true(self, db):
        user = UserFactory()
        assert user.safe_messaging_mode is True

    def test_default_location_sharing_is_false(self, db):
        user = UserFactory()
        assert user.location_sharing is False

    def test_sexual_orientation_visibility_defaults_to_only_me(self, db):
        user = UserFactory()
        assert user.sexual_orientation_visibility == "only_me"

    def test_is_private_property(self, db):
        user = UserFactory(private=True)
        assert user.is_private is True
        assert user.is_public is False

    def test_is_public_property(self, db):
        user = UserFactory(public=True)
        assert user.is_public is True
        assert user.is_private is False

    def test_get_display_name_falls_back_to_username(self, db):
        user = UserFactory()
        user.display_name = ""
        assert user.get_display_name() == user.username

    def test_inactive_trait(self, inactive_user):
        assert inactive_user.is_active is False


class TestFollowModel:
    def test_follow_str(self, db):
        a = UserFactory()
        b = UserFactory()
        follow = Follow.objects.create(follower=a, following=b, status="accepted")
        assert a.username in str(follow)

    def test_unique_together(self, db):
        a = UserFactory()
        b = UserFactory()
        Follow.objects.create(follower=a, following=b)
        with pytest.raises(IntegrityError):
            Follow.objects.create(follower=a, following=b)


class TestBlockedUserModel:
    def test_block_str(self, db):
        a = UserFactory()
        b = UserFactory()
        block = BlockedUser.objects.create(blocker=a, blocked=b)
        assert a.username in str(block)