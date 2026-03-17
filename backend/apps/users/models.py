# 📁 Location: backend/apps/users/models.py

from __future__ import annotations

import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.users.constants import (
    AccountPrivacyChoices,
    FollowStatusChoices,
    GenderIdentityChoices,
    PronounChoices,
    SexualOrientationChoices,
    VisibilityChoices,
)
from apps.users.managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom Qommunity User model.

    Key decisions
    -------------
    - UUID primary key          → non-guessable, safe in URLs and events
    - Email login               → more inclusive than username-only auth
    - LGBTQ+ identity fields    → first-class, with per-field visibility
    - Privacy-first defaults    → new accounts start as followers_only
    - Soft deactivation         → is_active=False hides user, preserves data
    """

    # ── Primary key ───────────────────────────────────────────────────────────
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # ── Core identity ─────────────────────────────────────────────────────────
    email    = models.EmailField(unique=True, db_index=True)
    username = models.CharField(max_length=30, unique=True, db_index=True)

    # ── Name ─────────────────────────────────────────────────────────────────
    first_name   = models.CharField(max_length=150, blank=True)
    last_name    = models.CharField(max_length=150, blank=True)
    display_name = models.CharField(
        max_length=60, blank=True,
        help_text="Optional name shown on profile; falls back to username.",
    )

    # ── Profile ───────────────────────────────────────────────────────────────
    bio            = models.TextField(max_length=500, blank=True)
    website        = models.URLField(blank=True)
    avatar         = models.ImageField(
        upload_to="avatars/", null=True, blank=True,
        help_text="Profile picture — wired to media app in M3.",
    )
    location       = models.CharField(max_length=100, blank=True)

    # ── LGBTQ+ identity fields (M2, Section 8) ────────────────────────────────
    pronouns = models.CharField(
        max_length=20,
        choices=PronounChoices.choices,
        blank=True,
    )
    pronouns_custom = models.CharField(
        max_length=50, blank=True,
        help_text="Used when pronouns=CUSTOM.",
    )
    pronouns_visibility = models.CharField(
        max_length=10,
        choices=VisibilityChoices.choices,
        default=VisibilityChoices.PUBLIC,
    )

    gender_identity = models.CharField(
        max_length=20,
        choices=GenderIdentityChoices.choices,
        blank=True,
    )
    gender_identity_custom = models.CharField(max_length=100, blank=True)
    gender_identity_visibility = models.CharField(
        max_length=10,
        choices=VisibilityChoices.choices,
        default=VisibilityChoices.FOLLOWERS,   # hidden from public by default
    )

    sexual_orientation = models.CharField(
        max_length=20,
        choices=SexualOrientationChoices.choices,
        blank=True,
    )
    sexual_orientation_custom = models.CharField(max_length=100, blank=True)
    sexual_orientation_visibility = models.CharField(
        max_length=10,
        choices=VisibilityChoices.choices,
        default=VisibilityChoices.ONLY_ME,   # outing prevention — hidden by default
    )

    # ── Privacy & safety (privacy-first defaults per roadmap) ─────────────────
    account_privacy = models.CharField(
        max_length=15,
        choices=AccountPrivacyChoices.choices,
        default=AccountPrivacyChoices.FOLLOWERS_ONLY,  # not public by default
    )
    safe_messaging_mode = models.BooleanField(
        default=True,
        help_text="Blur images from non-followers; require follow before DM.",
    )
    location_sharing = models.BooleanField(
        default=False,
        help_text="Opt-in only — never shared by default.",
    )

    # ── Account status ────────────────────────────────────────────────────────
    is_active   = models.BooleanField(default=True)
    is_staff    = models.BooleanField(default=False)
    is_verified = models.BooleanField(
        default=False,
        help_text="Email verified.",
    )

    # ── Timestamps ────────────────────────────────────────────────────────────
    date_joined = models.DateTimeField(default=timezone.now)
    last_seen   = models.DateTimeField(null=True, blank=True)

    # ── Manager & auth config ─────────────────────────────────────────────────
    objects = UserManager()

    USERNAME_FIELD  = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        db_table  = "users_user"
        ordering  = ["-date_joined"]
        indexes   = [
            models.Index(fields=["email"]),
            models.Index(fields=["username"]),
            models.Index(fields=["is_active", "date_joined"]),
        ]

    def __str__(self) -> str:
        return self.email

    def get_full_name(self) -> str:
        full = f"{self.first_name} {self.last_name}".strip()
        return full or self.username

    def get_display_name(self) -> str:
        return self.display_name or self.username

    @property
    def is_private(self) -> bool:
        return self.account_privacy == AccountPrivacyChoices.PRIVATE

    @property
    def is_public(self) -> bool:
        return self.account_privacy == AccountPrivacyChoices.PUBLIC


class Follow(models.Model):
    """
    Directed follow relationship: follower → following.

    For private accounts, status starts as PENDING and must be accepted.
    For public accounts, status goes straight to ACCEPTED.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    follower  = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="following_set",
    )
    following = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="follower_set",
    )
    status = models.CharField(
        max_length=10,
        choices=FollowStatusChoices.choices,
        default=FollowStatusChoices.ACCEPTED,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table       = "users_follow"
        unique_together = [("follower", "following")]
        indexes        = [
            models.Index(fields=["follower", "status"]),
            models.Index(fields=["following", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.follower.username} → {self.following.username} ({self.status})"


class BlockedUser(models.Model):
    """
    User A blocks user B.
    Blocked users cannot see A's profile, posts, or interact with them.
    Block is immediate and non-notifying.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    blocker  = models.ForeignKey(User, on_delete=models.CASCADE, related_name="blocking_set")
    blocked  = models.ForeignKey(User, on_delete=models.CASCADE, related_name="blocked_by_set")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table       = "users_blocked"
        unique_together = [("blocker", "blocked")]
        indexes        = [
            models.Index(fields=["blocker"]),
            models.Index(fields=["blocked"]),
        ]

    def __str__(self) -> str:
        return f"{self.blocker.username} blocked {self.blocked.username}"


class MutedUser(models.Model):
    """
    User A mutes user B.
    Muted users' posts don't appear in A's feed.
    The muted user has no idea they are muted (unlike block).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    muter  = models.ForeignKey(User, on_delete=models.CASCADE, related_name="muting_set")
    muted  = models.ForeignKey(User, on_delete=models.CASCADE, related_name="muted_by_set")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table       = "users_muted"
        unique_together = [("muter", "muted")]

    def __str__(self) -> str:
        return f"{self.muter.username} muted {self.muted.username}"


class UserReport(models.Model):
    """Allows users to report abusive/unsafe accounts."""

    class Reason(models.TextChoices):
        HATE_SPEECH    = "hate_speech",    "Hate speech / homophobia / transphobia"
        HARASSMENT     = "harassment",     "Harassment or bullying"
        SPAM           = "spam",           "Spam"
        IMPERSONATION  = "impersonation",  "Impersonation"
        OUTING         = "outing",         "Outing someone without consent"
        OTHER          = "other",          "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    reporter   = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reports_filed")
    reported   = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reports_received")
    reason     = models.CharField(max_length=20, choices=Reason.choices)
    details    = models.TextField(blank=True, max_length=1000)
    reviewed   = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "users_report"
        indexes  = [models.Index(fields=["reported", "reviewed"])]

    def __str__(self) -> str:
        return f"Report: {self.reporter.username} → {self.reported.username} ({self.reason})"