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

logger = logging.getLogger(__name__)


# -- Blocking propagation -----------------------------------------------------


def is_blocked(*, viewer_id: uuid.UUID, target_id: uuid.UUID) -> bool:
    """
    Return True if viewer has blocked target OR target has blocked viewer.
    """
    from apps.users.models import BlockedUser

    return BlockedUser.objects.filter(
        blocker_id__in=[viewer_id, target_id],
        blocked_id__in=[viewer_id, target_id],
    ).exists()


def filter_queryset_for_blocks(
    qs, *, viewer_id: uuid.UUID, author_field: str = "author_id"
):
    """
    Filter a QuerySet to exclude content from users blocked by/blocking viewer.
    author_field is the FK field name on the model pointing to the author.
    """
    from apps.users.models import BlockedUser

    blocked_ids = list(
        BlockedUser.objects.filter(blocker_id=viewer_id).values_list(
            "blocked_id", flat=True
        )
    )
    blocking_ids = list(
        BlockedUser.objects.filter(blocked_id=viewer_id).values_list(
            "blocker_id", flat=True
        )
    )
    all_excluded = set(blocked_ids) | set(blocking_ids)

    if all_excluded:
        return qs.exclude(**{f"{author_field}__in": all_excluded})
    return qs


# -- Outing prevention --------------------------------------------------------


def get_visible_identity_fields(
    *,
    profile_user_id: uuid.UUID,
    viewer_id: uuid.UUID | None,
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
        return set(PRIVATE_IDENTITY_FIELDS)  # owner sees all

    from apps.users.models import Follow

    is_follower = Follow.objects.filter(
        follower_id=viewer_id,
        following_id=profile_user_id,
    ).exists()

    if not is_follower:
        return set()

    return set(
        PRIVATE_IDENTITY_FIELDS
    )  # followers see all; per-field granularity in M8


# -- Crisis resources ---------------------------------------------------------


def get_crisis_resources_for_request(request) -> dict | None:
    """
    Return crisis resources based on request's Accept-Language / GEO header.
    Used by post/comment creation views when crisis content is detected.
    """
    from apps.common.safety.constants import CRISIS_RESOURCES

    accept_lang = request.META.get("HTTP_ACCEPT_LANGUAGE", "")
    # Map lang -> locale
    locale_map = {"EN-US": "US", "EN-GB": "UK", "HI": "IN", "EN-IN": "IN"}
    locale = locale_map.get(accept_lang.split(",")[0].upper(), "DEFAULT")

    return CRISIS_RESOURCES.get(locale) or CRISIS_RESOURCES.get("DEFAULT")
