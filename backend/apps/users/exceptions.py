# 📁 Location: backend/apps/users/exceptions.py

from core.exceptions.base import (
    AuthenticationError,
    BadRequestError,
    ConflictError,
    NotFoundError,
)


class UserNotFoundError(NotFoundError):
    code = "USER_NOT_FOUND"
    message = "User not found."


class EmailAlreadyExistsError(ConflictError):
    code = "EMAIL_TAKEN"
    message = "A user with this email address already exists."


class UsernameAlreadyExistsError(ConflictError):
    code = "USERNAME_TAKEN"
    message = "This username is already taken."


class InvalidCredentialsError(AuthenticationError):
    code = "INVALID_CREDENTIALS"
    message = "Incorrect email or password."


class AccountInactiveError(AuthenticationError):
    code = "ACCOUNT_INACTIVE"
    message = "This account has been deactivated."


class CannotFollowSelfError(BadRequestError):
    code = "CANNOT_FOLLOW_SELF"
    message = "You cannot follow yourself."


class AlreadyFollowingError(ConflictError):
    code = "ALREADY_FOLLOWING"
    message = "You are already following this user."


class NotFollowingError(BadRequestError):
    code = "NOT_FOLLOWING"
    message = "You are not following this user."


class AlreadyBlockedError(ConflictError):
    code = "ALREADY_BLOCKED"
    message = "You have already blocked this user."


class NotBlockedError(BadRequestError):
    code = "NOT_BLOCKED"
    message = "You have not blocked this user."
