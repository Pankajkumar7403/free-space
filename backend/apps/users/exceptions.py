from core.exceptions.base import ConflictError, AuthenticationError, NotFoundError


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