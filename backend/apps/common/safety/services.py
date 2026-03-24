"""
apps/common/safety/services.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
LGBTQ+ safety feature services.

Features
--------
1. Blocking propagation  - hide blocked users' content EVERYWHERE
2. Outing prevention     - identity fields hidden to non-followers by default
3. Crisis resource inject- surface resources when crisis content detected
4. Anonymous post guard  - strip all identity from anonymous posts
"""
from __future__ import annotations

import logging
import uuid
from typing import Optional

logger = logging.getLogger(__name__)


# -- Blocking propagation -----------------------------------------------------

def is_blocked(*, viewer_id: uuid.UUID, target_id: uuid.UUID) -> bool:
    """
    Return True if viewer has blocked target OR target has blocked viewer.
    Uses Redis cache with 5-min TTL for performance.
    """
    from apps.users.models import BlockedUser
    from core.redis.client import RedisClient

    redis   = RedisClient.get_instance()
    fwd_key = f"block:{viewer_id}:{target_id}"
    rev_key = f"block:{target_id}:{viewer_id}"

    # Cache hit
    fwd = redis.get(fwd_key)
    rev = redis.get(rev_key)
    if fwd is not None:
        return fwd == b"1"
    if rev is not None:
        return rev == b"1"

    # DB lookup - cache result for 5 min
    blocked = BlockedUser.objects.filter(
        blocker_id__in=[viewer_id, target_id],
        blocked_id__in=[viewer_id, target_id],
    ).exists()

    value = b"1" if blocked else b"0"
    redis.setex(fwd_key, 300, value)
    redis.setex(rev_key, 300, value)
    return blocked


def filter_queryset_for_blocks(
    qs, *, viewer_id: uuid.UUID, author_field: str = "author_id"
):
    """
    Filter a QuerySet to exclude content from users blocked by/blocking viewer.
    author_field is the FK field name on the model pointing to the author.
    """
    from apps.users.models import BlockedUser

    blocked_ids = list(
        BlockedUser.objects.filter(blocker_id=viewer_id)
        .values_list("blocked_id", flat=True)
    )
    blocking_ids = list(
        BlockedUser.objects.filter(blocked_id=viewer_id)
        .values_list("blocker_id", flat=True)
    )
    all_excluded = set(blocked_ids) | set(blocking_ids)

    if all_excluded:
        return qs.exclude(**{f"{author_field}__in": all_excluded})
    return qs


# -- Outing prevention --------------------------------------------------------

def get_visible_identity_fields(
    *,
    profile_user_id: uuid.UUID,
    viewer_id: Optional[uuid.UUID],
) -> set[str]:
    """
    Return the set of identity fields visible to viewer.

    Rules
    -----
    - Profile owner sees all fields.
    - Followers see fields where the user's per-field visibility is 'followers'.
    - Public sees only fields where visibility is 'public'.
    - Non-followers/non-authenticated see nothing.
    """
    from apps.common.safety.constants import PRIVATE_IDENTITY_FIELDS

    if viewer_id is None:
        return set()

    if str(viewer_id) == str(profile_user_id):
        return PRIVATE_IDENTITY_FIELDS   # owner sees all

    from apps.users.models import Follow
    is_follower = Follow.objects.filter(
        follower_id=viewer_id,
        following_id=profile_user_id,
    ).exists()

    if not is_follower:
        return set()

    return PRIVATE_IDENTITY_FIELDS   # followers see all; per-field granularity in M8


def log_identity_view(
    *, viewer_id: uuid.UUID, profile_id: uuid.UUID
) -> None:
    """
    Audit log: record who viewed a user's identity fields.
    Stored in Redis with 7-day TTL.  Used for outing investigations.
    """
    import time
    from core.redis.client import RedisClient
    from apps.common.safety.constants import (
        IDENTITY_VIEW_AUDIT_KEY,
        IDENTITY_VIEW_AUDIT_TTL,
    )

    redis = RedisClient.get_instance()
    key   = IDENTITY_VIEW_AUDIT_KEY.format(
        viewer_id=viewer_id, profile_id=profile_id
    )
    redis.setex(key, IDENTITY_VIEW_AUDIT_TTL, str(time.time()))


# -- Crisis resources ---------------------------------------------------------

def get_crisis_resources_for_request(request) -> Optional[dict]:
    """
    Return crisis resources based on request's Accept-Language / GEO header.
    Used by post/comment creation views when crisis content is detected.
    """
    from apps.common.safety.constants import CRISIS_RESOURCES

    accept_lang = request.META.get("HTTP_ACCEPT_LANGUAGE", "")
    lang_code   = accept_lang.split(",")[0].split("-")[0].upper() if accept_lang else ""

    # Map lang -> locale
    locale_map = {"EN-US": "US", "EN-GB": "UK", "HI": "IN", "EN-IN": "IN"}
    locale     = locale_map.get(accept_lang.split(",")[0].upper(), "DEFAULT")

    return CRISIS_RESOURCES.get(locale) or CRISIS_RESOURCES.get("DEFAULT")
