# 📁 Location: backend/apps/users/tests/test_services.py
# ▶  Run:      pytest apps/users/tests/test_services.py -v

from unittest.mock import patch

import pytest

from apps.users.exceptions import (
    AccountInactiveError,
    AlreadyBlockedError,
    AlreadyFollowingError,
    CannotFollowSelfError,
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    NotFollowingError,
    UsernameAlreadyExistsError,
    UserNotFoundError,
)
from apps.users.models import BlockedUser, Follow
from apps.users.services import (
    CreateUserInput,
    UpdateProfileInput,
    accept_follow_request,
    authenticate_user,
    block_user,
    create_user,
    follow_user,
    unblock_user,
    unfollow_user,
    update_profile,
)
from apps.users.tests.factories import UserFactory

pytestmark = [pytest.mark.unit, pytest.mark.django_db]


class TestCreateUser:
    def test_creates_user(self, db):
        user = create_user(
            CreateUserInput(
                email="new@example.com", username="newuser", password="pass1234"
            )
        )
        assert user.pk is not None
        assert user.email == "new@example.com"

    def test_password_is_hashed(self, db):
        user = create_user(
            CreateUserInput(
                email="hash@example.com", username="hashuser", password="pass1234"
            )
        )
        assert user.check_password("pass1234")
        assert user.password != "pass1234"

    def test_raises_on_duplicate_email(self, db):
        UserFactory(email="taken@example.com")
        with pytest.raises(EmailAlreadyExistsError):
            create_user(
                CreateUserInput(
                    email="taken@example.com", username="other", password="pass1234"
                )
            )

    def test_raises_on_duplicate_username(self, db):
        UserFactory(username="taken")
        with pytest.raises(UsernameAlreadyExistsError):
            create_user(
                CreateUserInput(
                    email="other@example.com", username="taken", password="pass1234"
                )
            )

    def test_email_check_case_insensitive(self, db):
        UserFactory(email="case@example.com")
        with pytest.raises(EmailAlreadyExistsError):
            create_user(
                CreateUserInput(
                    email="CASE@EXAMPLE.COM", username="other2", password="pass1234"
                )
            )

    def test_default_privacy_is_followers_only(self, db):
        user = create_user(
            CreateUserInput(
                email="priv@example.com", username="privuser", password="pass1234"
            )
        )
        assert user.account_privacy == "followers_only"


class TestAuthenticateUser:
    def test_returns_user_on_valid_credentials(self, db):
        u = UserFactory()
        u.set_password("correct")
        u.save()
        result = authenticate_user(email=u.email, password="correct")
        assert result.pk == u.pk

    def test_raises_on_wrong_password(self, db):
        u = UserFactory()
        u.set_password("correct")
        u.save()
        with pytest.raises(InvalidCredentialsError):
            authenticate_user(email=u.email, password="wrong")

    def test_raises_on_unknown_email(self, db):
        with pytest.raises(InvalidCredentialsError):
            authenticate_user(email="ghost@example.com", password="anything")

    def test_raises_on_inactive_account(self, inactive_user):
        inactive_user.set_password("pass")
        inactive_user.save()
        with pytest.raises(AccountInactiveError):
            authenticate_user(email=inactive_user.email, password="pass")


class TestUpdateProfile:
    def test_updates_username(self, user):
        updated = update_profile(
            user_id=user.pk, data=UpdateProfileInput(username="newhandle")
        )
        assert updated.username == "newhandle"

    def test_raises_on_username_conflict(self, user, db):
        UserFactory(username="occupied")
        with pytest.raises(UsernameAlreadyExistsError):
            update_profile(
                user_id=user.pk, data=UpdateProfileInput(username="occupied")
            )

    def test_updates_identity_fields(self, user):
        updated = update_profile(
            user_id=user.pk,
            data=UpdateProfileInput(
                pronouns="they/them",
                pronouns_visibility="public",
            ),
        )
        assert updated.pronouns == "they/them"
        assert updated.pronouns_visibility == "public"

    def test_raises_for_nonexistent_user(self, db):
        import uuid

        with pytest.raises(UserNotFoundError):
            update_profile(user_id=uuid.uuid4(), data=UpdateProfileInput(bio="ghost"))


class TestFollowServices:
    def test_follow_public_user_is_accepted(self, db):
        a = UserFactory(public=True)
        b = UserFactory(public=True)
        follow = follow_user(follower_id=a.pk, following_id=b.pk)
        assert follow.status == "accepted"

    def test_follow_private_user_is_pending(self, db):
        a = UserFactory()
        b = UserFactory(private=True)
        follow = follow_user(follower_id=a.pk, following_id=b.pk)
        assert follow.status == "pending"

    def test_follow_public_user_emits_user_followed_event(self, db):
        a = UserFactory(public=True)
        b = UserFactory(public=True)

        with patch("apps.users.services.emit_user_followed") as mock_emit:
            follow = follow_user(follower_id=a.pk, following_id=b.pk)

        assert follow.status == "accepted"
        mock_emit.assert_called_once_with(follower_id=str(a.pk), following_id=str(b.pk))

    def test_follow_private_user_does_not_emit_user_followed_event(self, db):
        a = UserFactory(public=True)
        b = UserFactory(private=True)

        with patch("apps.users.services.emit_user_followed") as mock_emit:
            follow = follow_user(follower_id=a.pk, following_id=b.pk)

        assert follow.status == "pending"
        mock_emit.assert_not_called()

    def test_accept_private_follow_request_emits_user_followed_event(self, db):
        follower = UserFactory(public=True)
        following = UserFactory(private=True)
        follow_user(follower_id=follower.pk, following_id=following.pk)

        with patch("apps.users.services.emit_user_followed") as mock_emit:
            follow = accept_follow_request(user_id=following.pk, follower_id=follower.pk)

        assert follow.status == "accepted"
        mock_emit.assert_called_once_with(
            follower_id=str(follower.pk),
            following_id=str(following.pk),
        )

    def test_cannot_follow_self(self, user):
        with pytest.raises(CannotFollowSelfError):
            follow_user(follower_id=user.pk, following_id=user.pk)

    def test_cannot_follow_twice(self, db):
        a = UserFactory(public=True)
        b = UserFactory(public=True)
        follow_user(follower_id=a.pk, following_id=b.pk)
        with pytest.raises(AlreadyFollowingError):
            follow_user(follower_id=a.pk, following_id=b.pk)

    def test_unfollow_removes_relationship(self, db):
        a = UserFactory(public=True)
        b = UserFactory(public=True)
        follow_user(follower_id=a.pk, following_id=b.pk)
        unfollow_user(follower_id=a.pk, following_id=b.pk)
        assert not Follow.objects.filter(follower=a, following=b).exists()

    def test_unfollow_raises_if_not_following(self, db):
        a = UserFactory()
        b = UserFactory()
        with pytest.raises(NotFollowingError):
            unfollow_user(follower_id=a.pk, following_id=b.pk)


class TestBlockServices:
    def test_block_removes_follow_relationships(self, db):
        a = UserFactory(public=True)
        b = UserFactory(public=True)
        follow_user(follower_id=a.pk, following_id=b.pk)
        follow_user(follower_id=b.pk, following_id=a.pk)
        block_user(blocker_id=a.pk, blocked_id=b.pk)
        assert not Follow.objects.filter(follower=a, following=b).exists()
        assert not Follow.objects.filter(follower=b, following=a).exists()

    def test_cannot_block_twice(self, db):
        a = UserFactory()
        b = UserFactory()
        block_user(blocker_id=a.pk, blocked_id=b.pk)
        with pytest.raises(AlreadyBlockedError):
            block_user(blocker_id=a.pk, blocked_id=b.pk)

    def test_unblock_removes_block(self, db):
        a = UserFactory()
        b = UserFactory()
        block_user(blocker_id=a.pk, blocked_id=b.pk)
        unblock_user(blocker_id=a.pk, blocked_id=b.pk)
        assert not BlockedUser.objects.filter(blocker=a, blocked=b).exists()
