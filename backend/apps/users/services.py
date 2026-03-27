# 📁 Location: backend/apps/users/services.py

from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction

from apps.users.exceptions import (
    AccountInactiveError,
    AlreadyBlockedError,
    AlreadyFollowingError,
    CannotFollowSelfError,
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    NotBlockedError,
    NotFollowingError,
    UsernameAlreadyExistsError,
    UserNotFoundError,
)
from apps.users.models import BlockedUser, Follow, MutedUser, User, UserReport
from apps.users.selectors import (
    email_exists,
    get_user_by_id,
    is_blocked,
    is_following,
    username_exists,
)
from apps.users.validators import (
    validate_bio,
    validate_password_strength,
    validate_username,
)

# ── Input dataclasses ─────────────────────────────────────────────────────────


@dataclass
class CreateUserInput:
    email: str
    username: str
    password: str
    first_name: str = ""
    last_name: str = ""


@dataclass
class UpdateProfileInput:
    display_name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    bio: str | None = None
    website: str | None = None
    username: str | None = None
    pronouns: str | None = None
    pronouns_custom: str | None = None
    pronouns_visibility: str | None = None
    gender_identity: str | None = None
    gender_identity_custom: str | None = None
    gender_identity_visibility: str | None = None
    sexual_orientation: str | None = None
    sexual_orientation_custom: str | None = None
    sexual_orientation_visibility: str | None = None
    account_privacy: str | None = None
    safe_messaging_mode: bool | None = None


# ── Auth services ─────────────────────────────────────────────────────────────


@transaction.atomic
def create_user(data: CreateUserInput) -> User:
    """
    Register a new user.

    Raises: EmailAlreadyExistsError, UsernameAlreadyExistsError
    """
    validate_username(data.username)
    validate_password_strength(data.password)

    if email_exists(data.email):
        raise EmailAlreadyExistsError()
    if username_exists(data.username):
        raise UsernameAlreadyExistsError()

    user = User.objects.create_user(
        email=data.email,
        username=data.username,
        password=data.password,
        first_name=data.first_name,
        last_name=data.last_name,
    )
    return user


def authenticate_user(*, email: str, password: str) -> User:
    """
    Verify credentials. Constant-time on failure to prevent timing attacks.

    Raises: InvalidCredentialsError, AccountInactiveError
    """
    try:
        user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        User().check_password(password)  # constant-time dummy check
        raise InvalidCredentialsError()

    if not user.check_password(password):
        raise InvalidCredentialsError()

    if not user.is_active:
        raise AccountInactiveError()

    return user


@transaction.atomic
def deactivate_user(*, user_id) -> None:
    """Soft-delete: marks is_active=False. Raises UserNotFoundError."""
    user = get_user_by_id(user_id)
    user.is_active = False
    user.save(update_fields=["is_active"])


# ── Profile services ──────────────────────────────────────────────────────────


@transaction.atomic
def update_profile(*, user_id, data: UpdateProfileInput) -> User:
    """
    Update mutable profile & identity fields.

    Raises: UserNotFoundError, UsernameAlreadyExistsError
    """
    user = get_user_by_id(user_id)
    updated_fields: list[str] = []

    # ── Username uniqueness check ─────────────────────────────────────────────
    if data.username is not None and data.username != user.username:
        validate_username(data.username)
        if username_exists(data.username):
            raise UsernameAlreadyExistsError()
        user.username = data.username
        updated_fields.append("username")

    # ── Simple string fields ──────────────────────────────────────────────────
    simple_fields = [
        "display_name",
        "first_name",
        "last_name",
        "website",
        "pronouns",
        "pronouns_custom",
        "pronouns_visibility",
        "gender_identity",
        "gender_identity_custom",
        "gender_identity_visibility",
        "sexual_orientation",
        "sexual_orientation_custom",
        "sexual_orientation_visibility",
        "account_privacy",
    ]

    for field in simple_fields:
        value = getattr(data, field)
        if value is not None:
            setattr(user, field, value)
            updated_fields.append(field)

    # ── Bio (has length validation) ───────────────────────────────────────────
    if data.bio is not None:
        validate_bio(data.bio)
        user.bio = data.bio
        updated_fields.append("bio")

    # ── Boolean fields ────────────────────────────────────────────────────────
    if data.safe_messaging_mode is not None:
        user.safe_messaging_mode = data.safe_messaging_mode
        updated_fields.append("safe_messaging_mode")

    if updated_fields:
        user.save(update_fields=updated_fields)

    user.refresh_from_db()
    return user


# ── Follow services ───────────────────────────────────────────────────────────


@transaction.atomic
def follow_user(*, follower_id, following_id) -> Follow:
    """
    Follow another user.

    - Public accounts  → status=accepted immediately
    - Private accounts → status=pending (requires accept_follow_request)

    Raises: UserNotFoundError, CannotFollowSelfError, AlreadyFollowingError
    """
    follower = get_user_by_id(follower_id)
    following = get_user_by_id(following_id)

    if follower.pk == following.pk:
        raise CannotFollowSelfError()

    if is_following(follower, following):
        raise AlreadyFollowingError()

    if is_blocked(following, follower):
        raise UserNotFoundError()  # treat blocked as not found (safety)

    from apps.users.constants import AccountPrivacyChoices, FollowStatusChoices

    status = (
        FollowStatusChoices.PENDING
        if following.account_privacy == AccountPrivacyChoices.PRIVATE
        else FollowStatusChoices.ACCEPTED
    )

    follow, _ = Follow.objects.get_or_create(
        follower=follower,
        following=following,
        defaults={"status": status},
    )
    return follow


@transaction.atomic
def unfollow_user(*, follower_id, following_id) -> None:
    """Raises: UserNotFoundError, NotFollowingError"""
    follower = get_user_by_id(follower_id)
    following = get_user_by_id(following_id)

    deleted, _ = Follow.objects.filter(follower=follower, following=following).delete()
    if not deleted:
        raise NotFollowingError()


@transaction.atomic
def accept_follow_request(*, user_id, follower_id) -> Follow:
    """Accept a pending follow request. *user_id* is the account owner."""
    from apps.users.constants import FollowStatusChoices

    try:
        follow = Follow.objects.get(
            follower_id=follower_id,
            following_id=user_id,
            status=FollowStatusChoices.PENDING,
        )
    except Follow.DoesNotExist:
        raise UserNotFoundError(detail={"follower_id": str(follower_id)})

    follow.status = FollowStatusChoices.ACCEPTED
    follow.save(update_fields=["status", "updated_at"])
    return follow


@transaction.atomic
def reject_follow_request(*, user_id, follower_id) -> None:
    """Reject and delete a pending follow request."""
    Follow.objects.filter(
        follower_id=follower_id,
        following_id=user_id,
        status="pending",
    ).delete()


# ── Block / Mute services ─────────────────────────────────────────────────────


@transaction.atomic
def block_user(*, blocker_id, blocked_id) -> BlockedUser:
    """
    Block a user. Also removes any follow relationship in both directions.

    Raises: UserNotFoundError, AlreadyBlockedError, CannotFollowSelfError
    """
    blocker = get_user_by_id(blocker_id)
    blocked = get_user_by_id(blocked_id)

    if blocker.pk == blocked.pk:
        raise CannotFollowSelfError(message="You cannot block yourself.")

    if is_blocked(blocker, blocked):
        raise AlreadyBlockedError()

    # Remove follow relationships in both directions
    Follow.objects.filter(follower=blocker, following=blocked).delete()
    Follow.objects.filter(follower=blocked, following=blocker).delete()

    block, _ = BlockedUser.objects.get_or_create(blocker=blocker, blocked=blocked)
    return block


@transaction.atomic
def unblock_user(*, blocker_id, blocked_id) -> None:
    """Raises: NotBlockedError"""
    blocker = get_user_by_id(blocker_id)
    blocked = get_user_by_id(blocked_id)

    deleted, _ = BlockedUser.objects.filter(blocker=blocker, blocked=blocked).delete()
    if not deleted:
        raise NotBlockedError()


@transaction.atomic
def mute_user(*, muter_id, muted_id) -> MutedUser:
    muter = get_user_by_id(muter_id)
    muted = get_user_by_id(muted_id)
    obj, _ = MutedUser.objects.get_or_create(muter=muter, muted=muted)
    return obj


@transaction.atomic
def unmute_user(*, muter_id, muted_id) -> None:
    muter = get_user_by_id(muter_id)
    muted = get_user_by_id(muted_id)
    MutedUser.objects.filter(muter=muter, muted=muted).delete()


# ── Report service ────────────────────────────────────────────────────────────


@transaction.atomic
def report_user(
    *, reporter_id, reported_id, reason: str, details: str = ""
) -> UserReport:
    reporter = get_user_by_id(reporter_id)
    reported = get_user_by_id(reported_id)
    return UserReport.objects.create(
        reporter=reporter,
        reported=reported,
        reason=reason,
        details=details,
    )
