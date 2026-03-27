# 📁 Location: backend/apps/feed/constants.py

from django.db import models


class FeedSource(models.TextChoices):
    """Where a feed item came from."""

    FOLLOW = "follow", "Followed user's post"
    HASHTAG = "hashtag", "Subscribed hashtag"
    EXPLORE = "explore", "Explore / recommended"


# ── Feed engine constants ─────────────────────────────────────────────────────

# Users with MORE than this many followers use fan-out-on-READ
# to avoid writing to millions of Redis keys on every post
CELEBRITY_FOLLOWER_THRESHOLD = 10_000

# Maximum posts kept per user's feed in Redis (ZSet)
FEED_MAX_SIZE = 1_000

# Feed TTL in seconds (7 days — inactive users' feeds expire)
FEED_TTL_SECONDS = 60 * 60 * 24 * 7

# Celery fanout: push to this many follower feeds per task batch
FANOUT_BATCH_SIZE = 100

# Ranking weights
WEIGHT_RECENCY = 0.6  # 60% recency
WEIGHT_ENGAGEMENT = 0.3  # 30% engagement (likes + comments)
WEIGHT_RELATIONSHIP = 0.1  # 10% relationship strength (mutual follow)
