# 📁 Location: backend/apps/feed/ranking.py

from __future__ import annotations

import math
import time
from datetime import datetime, timezone

from apps.feed.constants import (
    WEIGHT_ENGAGEMENT,
    WEIGHT_RECENCY,
    WEIGHT_RELATIONSHIP,
)


def compute_score(
    *,
    post_created_at: datetime,
    like_count: int = 0,
    comment_count: int = 0,
    is_mutual_follow: bool = False,
    now: datetime | None = None,
) -> float:
    """
    Compute a ranking score for a post in a user's feed.

    Score formula
    -------------
    score = (recency * 0.6) + (engagement * 0.3) + (relationship * 0.1)

    Components
    ----------
    recency
        Decays exponentially with age. A post from 1 hour ago scores
        ~0.97. A post from 24 hours ago scores ~0.50. A post from
        7 days ago scores near 0.

    engagement
        log(likes + comments + 1) normalised to [0, 1] against a
        "viral" ceiling of 1000 interactions.

    relationship
        Binary: 0.0 for one-way follow, 1.0 for mutual follow.
        Mutual connections see each other's posts ranked slightly higher.

    Returns
    -------
    float in [0.0, 1.0]
    """
    if now is None:
        now = datetime.now(timezone.utc)

    # ── Recency ───────────────────────────────────────────────────────────────
    # Half-life of 24 hours: score * 0.5 every 24h
    age_hours = (now - post_created_at).total_seconds() / 3600
    half_life = 24.0
    recency = math.exp(-math.log(2) * age_hours / half_life)

    # ── Engagement ────────────────────────────────────────────────────────────
    total_interactions = like_count + comment_count
    viral_ceiling = 1000.0
    engagement = math.log1p(total_interactions) / math.log1p(viral_ceiling)
    engagement = min(engagement, 1.0)

    # ── Relationship strength ─────────────────────────────────────────────────
    relationship = 1.0 if is_mutual_follow else 0.0

    score = (
        WEIGHT_RECENCY      * recency
        + WEIGHT_ENGAGEMENT * engagement
        + WEIGHT_RELATIONSHIP * relationship
    )
    return round(score, 6)


def recency_score(post_created_at: datetime, now: datetime | None = None) -> float:
    """
    Simplified recency-only score used for explore and hashtag feeds.
    Returns Unix timestamp normalised so newer posts sort first.
    """
    return post_created_at.timestamp()