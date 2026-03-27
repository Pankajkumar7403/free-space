# 📁 Location: backend/apps/feed/tests/test_ranking.py
# ▶  Run:      pytest apps/feed/tests/test_ranking.py -v

from datetime import UTC, datetime, timedelta

import pytest

from apps.feed.ranking import compute_score, recency_score

pytestmark = pytest.mark.unit


class TestComputeScore:

    def _now(self):
        return datetime(2025, 6, 1, 12, 0, 0, tzinfo=UTC)

    def test_brand_new_post_has_high_score(self):
        now = self._now()
        score = compute_score(
            post_created_at=now - timedelta(minutes=1),
            now=now,
        )
        assert score > 0.55  # almost entirely recency weight

    def test_old_post_has_low_score(self):
        now = self._now()
        score = compute_score(
            post_created_at=now - timedelta(days=14),
            now=now,
        )
        assert score < 0.05  # decayed to near zero

    def test_engagement_boosts_score(self):
        now = self._now()
        low = compute_score(
            post_created_at=now - timedelta(hours=1), like_count=0, now=now
        )
        high = compute_score(
            post_created_at=now - timedelta(hours=1), like_count=500, now=now
        )
        assert high > low

    def test_mutual_follow_boosts_score(self):
        now = self._now()
        one_way = compute_score(
            post_created_at=now - timedelta(hours=1), is_mutual_follow=False, now=now
        )
        mutual = compute_score(
            post_created_at=now - timedelta(hours=1), is_mutual_follow=True, now=now
        )
        assert mutual > one_way

    def test_score_is_between_zero_and_one(self):
        now = self._now()
        for hours_ago in [0, 1, 6, 24, 72, 168]:
            score = compute_score(
                post_created_at=now - timedelta(hours=hours_ago),
                like_count=100,
                comment_count=50,
                is_mutual_follow=True,
                now=now,
            )
            assert (
                0.0 <= score <= 1.0
            ), f"score={score} out of range for hours_ago={hours_ago}"

    def test_score_decreases_with_age(self):
        now = self._now()
        scores = [
            compute_score(post_created_at=now - timedelta(hours=h), now=now)
            for h in [1, 6, 12, 24, 48]
        ]
        for i in range(len(scores) - 1):
            assert (
                scores[i] > scores[i + 1]
            ), f"score at index {i} not greater than {i+1}"

    def test_viral_post_engagement_capped_at_1(self):
        now = self._now()
        score_1k = compute_score(post_created_at=now, like_count=1_000, now=now)
        score_10k = compute_score(post_created_at=now, like_count=10_000, now=now)
        assert abs(score_1k - score_10k) < 0.001

    def test_recency_score_returns_timestamp(self):
        dt = datetime(2025, 1, 1, tzinfo=UTC)
        score = recency_score(dt)
        assert score == dt.timestamp()
        assert isinstance(score, float)
