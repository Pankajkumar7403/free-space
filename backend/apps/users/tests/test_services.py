# 📁 Location: backend/apps/users/tests/test_services.py
# ▶  Run:      pytest apps/users/tests/test_services.py -v
"""
Test services (write operations).

These are unit tests — they hit the DB but do no HTTP.
External side-effects (email, Kafka) are mocked.
"""
import pytest
from django.contrib.auth import get_user_model

from apps.users.exceptions import (
    AccountInactiveError,
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    UsernameAlreadyExistsError,
    UserNotFoundError,
)
from apps.users.services import (
    CreateUserInput,
    UpdateUserInput,
    authenticate_user,
    create_user,
    deactivate_user,
    update_user,
)
from apps.users.tests.factories import UserFactory

User = get_user_model()

pytestmark = [pytest.mark.unit, pytest.mark.django_db]


class TestCreateUser:
    def _make_input(self, **overrides) -> CreateUserInput:
        defaults = dict(
            email="newuser@example.com",
            username="newuser",
            password="securepass123",
        )
        defaults.update(overrides)
        return CreateUserInput(**defaults)

    def test_creates_user_successfully(self, db):
        data = self._make_input()
        user = create_user(data)

        assert user.pk is not None
        assert user.email == "newuser@example.com"
        assert user.username == "newuser"
        # Password should be hashed, never stored plaintext
        assert user.password != "securepass123"
        assert user.check_password("securepass123")

    def test_raises_on_duplicate_email(self, db):
        existing = UserFactory(email="taken@example.com")
        data = self._make_input(email="taken@example.com", username="different_user")

        with pytest.raises(EmailAlreadyExistsError):
            create_user(data)

    def test_raises_on_duplicate_username(self, db):
        UserFactory(username="takenname")
        data = self._make_input(email="different@example.com", username="takenname")

        with pytest.raises(UsernameAlreadyExistsError):
            create_user(data)

    def test_email_check_is_case_insensitive(self, db):
        UserFactory(email="taken@example.com")
        data = self._make_input(email="TAKEN@EXAMPLE.COM", username="other")

        with pytest.raises(EmailAlreadyExistsError):
            create_user(data)


class TestUpdateUser:
    def test_updates_username(self, user):
        updated = update_user(user_id=user.pk, data=UpdateUserInput(username="new_handle"))
        assert updated.username == "new_handle"

    def test_updates_name_fields(self, user):
        updated = update_user(
            user_id=user.pk,
            data=UpdateUserInput(first_name="Alice", last_name="Smith"),
        )
        assert updated.first_name == "Alice"
        assert updated.last_name == "Smith"

    def test_raises_on_username_conflict(self, user):
        other = UserFactory(username="occupied")
        with pytest.raises(UsernameAlreadyExistsError):
            update_user(user_id=user.pk, data=UpdateUserInput(username="occupied"))

    def test_raises_when_user_not_found(self):
        with pytest.raises(UserNotFoundError):
            update_user(user_id=99999, data=UpdateUserInput(first_name="Ghost"))

    def test_same_username_does_not_conflict(self, user):
        """A user should be able to 'update' with their existing username."""
        updated = update_user(user_id=user.pk, data=UpdateUserInput(username=user.username))
        assert updated.username == user.username


class TestDeactivateUser:
    def test_deactivates_user(self, user):
        deactivate_user(user_id=user.pk)
        user.refresh_from_db()
        assert user.is_active is False

    def test_raises_when_already_inactive(self, inactive_user):
        with pytest.raises(UserNotFoundError):
            deactivate_user(user_id=inactive_user.pk)


class TestAuthenticateUser:
    def test_returns_user_on_valid_credentials(self, db):
        user = UserFactory()
        user.set_password("correct_password")
        user.save()

        result = authenticate_user(email=user.email, password="correct_password")
        assert result.pk == user.pk

    def test_raises_on_wrong_password(self, db):
        user = UserFactory()
        user.set_password("correct")
        user.save()

        with pytest.raises(InvalidCredentialsError):
            authenticate_user(email=user.email, password="wrong")

    def test_raises_on_unknown_email(self, db):
        with pytest.raises(InvalidCredentialsError):
            authenticate_user(email="ghost@example.com", password="anything")

    def test_raises_on_inactive_account(self, inactive_user):
        inactive_user.set_password("pass")
        inactive_user.save()

        with pytest.raises(AccountInactiveError):
            authenticate_user(email=inactive_user.email, password="pass")

    def test_email_check_is_case_insensitive(self, db):
        user = UserFactory(email="case@example.com")
        user.set_password("pass")
        user.save()

        result = authenticate_user(email="CASE@EXAMPLE.COM", password="pass")
        assert result.pk == user.pk