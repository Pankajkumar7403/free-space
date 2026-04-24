# 📁 Location: backend/apps/users/services.py

from __future__ import annotations

import base64
import json
import secrets
from dataclasses import dataclass
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.cache import cache
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
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
from apps.users.events import emit_user_followed
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


PASSWORD_RESET_TTL_SECONDS = 15 * 60
EMAIL_VERIFY_TTL_SECONDS = 15 * 60
_signer = TimestampSigner(salt="users.auth.otp")


def _generate_numeric_code(length: int = 6) -> str:
    return "".join(secrets.choice("0123456789") for _ in range(length))


def _cache_key(prefix: str, token: str) -> str:
    return f"users:{prefix}:{token}"


def issue_password_reset_code(*, email: str) -> None:
    """
    Generate a one-time reset code for *email* and cache it.
    Always no-op silently when email is unknown to prevent enumeration.
    """
    try:
        user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        return

    otp = _generate_numeric_code()
    signed = _signer.sign(f"pwd:{user.email.lower()}:{otp}")
    cache.set(_cache_key("pwd-reset", otp), signed, timeout=PASSWORD_RESET_TTL_SECONDS)


def reset_password_with_otp(*, otp: str, new_password: str) -> None:
    """Validate OTP and set the new password."""
    token = cache.get(_cache_key("pwd-reset", otp))
    if not token:
        raise InvalidCredentialsError(message="Invalid or expired reset code.")

    try:
        payload = _signer.unsign(token, max_age=PASSWORD_RESET_TTL_SECONDS)
    except (BadSignature, SignatureExpired):
        cache.delete(_cache_key("pwd-reset", otp))
        raise InvalidCredentialsError(message="Invalid or expired reset code.")

    parts = payload.split(":")
    if len(parts) != 3 or parts[0] != "pwd":
        raise InvalidCredentialsError(message="Invalid reset code payload.")

    user = User.objects.filter(email__iexact=parts[1]).first()
    if user is None:
        raise UserNotFoundError()

    validate_password_strength(new_password)
    user.set_password(new_password)
    user.save(update_fields=["password"])
    cache.delete(_cache_key("pwd-reset", otp))


def issue_email_verification_code(*, email: str) -> None:
    """Generate a short-lived code for email verification."""
    user = User.objects.filter(email__iexact=email).first()
    if user is None:
        return
    otp = _generate_numeric_code()
    signed = _signer.sign(f"verify:{user.email.lower()}:{otp}")
    cache.set(_cache_key("email-verify", otp), signed, timeout=EMAIL_VERIFY_TTL_SECONDS)


def verify_email_with_otp(*, otp: str, email: str) -> None:
    token = cache.get(_cache_key("email-verify", otp))
    if not token:
        raise InvalidCredentialsError(message="Invalid or expired verification code.")
    try:
        payload = _signer.unsign(token, max_age=EMAIL_VERIFY_TTL_SECONDS)
    except (BadSignature, SignatureExpired):
        cache.delete(_cache_key("email-verify", otp))
        raise InvalidCredentialsError(message="Invalid or expired verification code.")

    parts = payload.split(":")
    if len(parts) != 3 or parts[0] != "verify" or parts[1] != email.lower():
        raise InvalidCredentialsError(message="Invalid verification code.")

    user = User.objects.filter(email__iexact=email).first()
    if user is None:
        raise UserNotFoundError()
    user.is_verified = True
    user.save(update_fields=["is_verified"])
    cache.delete(_cache_key("email-verify", otp))


_SUPPORTED_OAUTH_PROVIDERS = {"google", "apple"}


def build_oauth_init_url(*, provider: str, redirect_uri: str) -> str:
    """Return provider authorization URL with signed CSRF state."""
    provider = provider.lower()
    if provider not in _SUPPORTED_OAUTH_PROVIDERS:
        raise InvalidCredentialsError(message="Unsupported OAuth provider.")

    state_payload = json.dumps(
        {
            "prefix": "oauth",
            "provider": provider,
            "redirect_uri": redirect_uri,
            "nonce": secrets.token_urlsafe(16),
        },
        separators=(",", ":"),
    )
    state_token = _signer.sign(state_payload)

    if provider == "google":
        client_id = getattr(settings, "GOOGLE_OAUTH_CLIENT_ID", "")
        if not client_id:
            raise InvalidCredentialsError(message="Google OAuth is not configured.")
        query = urlencode(
            {
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": "openid email profile",
                "access_type": "offline",
                "prompt": "consent",
                "state": state_token,
            }
        )
        return f"https://accounts.google.com/o/oauth2/v2/auth?{query}"

    client_id = getattr(settings, "APPLE_OAUTH_CLIENT_ID", "")
    if not client_id:
        raise InvalidCredentialsError(message="Apple OAuth is not configured.")
    query = urlencode(
        {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "response_mode": "query",
            "scope": "name email",
            "state": state_token,
        }
    )
    return f"https://appleid.apple.com/auth/authorize?{query}"


def _http_post_form(url: str, data: dict[str, str]) -> dict:
    encoded = urlencode(data).encode("utf-8")
    req = Request(url=url, data=encoded, headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urlopen(req, timeout=10) as response:  # noqa: S310
        return json.loads(response.read().decode("utf-8"))


def _http_get_json(url: str, headers: dict[str, str] | None = None) -> dict:
    req = Request(url=url, headers=headers or {})
    with urlopen(req, timeout=10) as response:  # noqa: S310
        return json.loads(response.read().decode("utf-8"))


def _decode_jwt_payload(token: str) -> dict:
    try:
        payload = token.split(".")[1]
        padding = "=" * (-len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload + padding)
        return json.loads(decoded.decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise InvalidCredentialsError(message="Invalid OAuth token payload.") from exc


@transaction.atomic
def oauth_login_or_register(
    *, provider: str, code: str, redirect_uri: str, state: str | None
) -> User:
    provider = provider.lower()
    if provider not in _SUPPORTED_OAUTH_PROVIDERS:
        raise InvalidCredentialsError(message="Unsupported OAuth provider.")

    if not state:
        raise InvalidCredentialsError(message="Missing OAuth state.")
    try:
        unsigned = _signer.unsign(state, max_age=10 * 60)
        payload = json.loads(unsigned)
    except (BadSignature, SignatureExpired, json.JSONDecodeError):
        raise InvalidCredentialsError(message="Invalid OAuth state.")

    if (
        payload.get("prefix") != "oauth"
        or payload.get("provider") != provider
        or payload.get("redirect_uri") != redirect_uri
    ):
        raise InvalidCredentialsError(message="OAuth state mismatch.")

    if provider == "google":
        token_data = _http_post_form(
            "https://oauth2.googleapis.com/token",
            {
                "code": code,
                "client_id": getattr(settings, "GOOGLE_OAUTH_CLIENT_ID", ""),
                "client_secret": getattr(settings, "GOOGLE_OAUTH_CLIENT_SECRET", ""),
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        access_token = token_data.get("access_token")
        if not access_token:
            raise InvalidCredentialsError(message="Google token exchange failed.")
        userinfo = _http_get_json(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        email = str(userinfo.get("email", "")).lower()
        username_seed = str(userinfo.get("name") or email.split("@")[0] or "googleuser")
    else:
        token_data = _http_post_form(
            "https://appleid.apple.com/auth/token",
            {
                "code": code,
                "client_id": getattr(settings, "APPLE_OAUTH_CLIENT_ID", ""),
                "client_secret": getattr(settings, "APPLE_OAUTH_CLIENT_SECRET", ""),
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        id_token = token_data.get("id_token")
        if not id_token:
            raise InvalidCredentialsError(message="Apple token exchange failed.")
        payload = _decode_jwt_payload(id_token)
        email = str(payload.get("email", "")).lower()
        username_seed = email.split("@")[0] if email else "appleuser"

    if not email:
        raise InvalidCredentialsError(message="OAuth provider did not return an email.")

    existing = User.objects.filter(email__iexact=email).first()
    if existing:
        return existing

    base_username = "".join(ch for ch in username_seed.lower() if ch.isalnum() or ch == "_")[:20] or "user"
    username = base_username
    counter = 1
    while User.objects.filter(username=username).exists():
        counter += 1
        username = f"{base_username[:16]}{counter}"

    user = User.objects.create_user(
        email=email,
        username=username,
        password=secrets.token_urlsafe(24),
    )
    user.is_verified = True
    user.save(update_fields=["is_verified"])
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
    if follow.status == FollowStatusChoices.ACCEPTED:
        emit_user_followed(follower_id=str(follower.pk), following_id=str(following.pk))
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
    emit_user_followed(follower_id=str(follower_id), following_id=str(user_id))
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
