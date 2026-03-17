# 📁 Location: backend/apps/users/selectors.py

from __future__ import annotations

from django.db.models import QuerySet

from apps.users.exceptions import UserNotFoundError
from apps.users.models import BlockedUser, Follow, MutedUser, User


# ── User lookups ──────────────────────────────────────────────────────────────

def get_user_by_id(user_id) -> User:
    """Raises UserNotFoundError if no active user with this id exists."""
    try:
        return User.objects.get(pk=user_id, is_active=True)
    except User.DoesNotExist:
        raise UserNotFoundError(detail={"user_id": str(user_id)})


def get_user_by_email(email: str) -> User:
    """Case-insensitive email lookup. Raises UserNotFoundError on miss."""
    try:
        return User.objects.get(email__iexact=email, is_active=True)
    except User.DoesNotExist:
        raise UserNotFoundError(detail={"email": email})


def get_user_by_username(username: str) -> User:
    """Case-insensitive username lookup. Raises UserNotFoundError on miss."""
    try:
        return User.objects.get(username__iexact=username, is_active=True)
    except User.DoesNotExist:
        raise UserNotFoundError(detail={"username": username})


def get_active_users() -> QuerySet:
    return User.objects.filter(is_active=True).order_by("-date_joined")


def email_exists(email: str) -> bool:
    return User.objects.filter(email__iexact=email).exists()


def username_exists(username: str) -> bool:
    return User.objects.filter(username__iexact=username).exists()


# ── Follow graph ──────────────────────────────────────────────────────────────

def get_followers(user: User) -> QuerySet:
    follower_ids = Follow.objects.filter(
        following=user, status="accepted"
    ).values_list("follower_id", flat=True)
    return User.objects.filter(pk__in=follower_ids, is_active=True)


def get_following(user: User) -> QuerySet:
    following_ids = Follow.objects.filter(
        follower=user, status="accepted"
    ).values_list("following_id", flat=True)
    return User.objects.filter(pk__in=following_ids, is_active=True)


def get_follower_count(user: User) -> int:
    return Follow.objects.filter(following=user, status="accepted").count()


def get_following_count(user: User) -> int:
    return Follow.objects.filter(follower=user, status="accepted").count()


def is_following(follower: User, following: User) -> bool:
    return Follow.objects.filter(
        follower=follower, following=following, status="accepted"
    ).exists()


def get_follow_requests(user: User) -> QuerySet:
    return Follow.objects.filter(
        following=user, status="pending"
    ).select_related("follower").order_by("-created_at")


# ── Block / Mute ──────────────────────────────────────────────────────────────

def get_blocked_users(user: User) -> QuerySet:
    blocked_ids = BlockedUser.objects.filter(blocker=user).values_list("blocked_id", flat=True)
    return User.objects.filter(pk__in=blocked_ids)


def get_muted_users(user: User) -> QuerySet:
    muted_ids = MutedUser.objects.filter(muter=user).values_list("muted_id", flat=True)
    return User.objects.filter(pk__in=muted_ids)


def is_blocked(blocker: User, blocked: User) -> bool:
    return BlockedUser.objects.filter(blocker=blocker, blocked=blocked).exists()


def is_muted(muter: User, muted: User) -> bool:
    return MutedUser.objects.filter(muter=muter, muted=muted).exists()


# ── Search ────────────────────────────────────────────────────────────────────

def search_users(query: str, exclude_user=None) -> QuerySet:
    qs = User.objects.filter(
        is_active=True,
        account_privacy__in=["public", "followers_only"],
    ).filter(username__icontains=query).order_by("username")

    if exclude_user:
        qs = qs.exclude(pk=exclude_user.pk)

    return qs[:50]