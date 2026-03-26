"""
core/tests/test_feature_flags.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Unit tests for Redis-based feature flag system.
No DB required - Redis is fully mocked.
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest

# -- Shared Redis mock fixture ------------------------------------------------


@pytest.fixture
def mock_redis():
    """
    Provide a mock Redis client.
    Default state: all flags disabled (returns None for gets, False for sismember).
    """
    redis = MagicMock()
    redis.get.return_value = None
    redis.sismember.return_value = False
    redis.scard.return_value = 0

    with patch("core.feature_flags.client._get_redis", return_value=redis):
        yield redis


# -- Global toggle ------------------------------------------------------------


class TestFeatureFlagGlobalToggle:

    def test_disabled_by_default(self, mock_redis):
        from core.feature_flags.client import FeatureFlag

        flag = FeatureFlag("my_feature")
        assert flag.check() is False

    def test_global_enable_returns_true(self, mock_redis):
        from core.feature_flags.client import FeatureFlag

        mock_redis.get.return_value = b"1"
        flag = FeatureFlag("my_feature")
        assert flag.check() is True

    def test_global_enable_calls_redis_set(self, mock_redis):
        from core.feature_flags.client import FeatureFlag

        flag = FeatureFlag("my_feature")
        flag.enable()
        mock_redis.set.assert_called_once()

    def test_global_disable_calls_pipeline_delete(self, mock_redis):
        from core.feature_flags.client import FeatureFlag

        pipe_mock = MagicMock()
        mock_redis.pipeline.return_value = pipe_mock
        flag = FeatureFlag("my_feature")
        flag.disable()
        mock_redis.pipeline.assert_called_once()
        pipe_mock.execute.assert_called_once()

    def test_global_flag_checked_before_user(self, mock_redis):
        """Global on should return True without even checking user."""
        from core.feature_flags.client import FeatureFlag

        mock_redis.get.return_value = b"1"
        flag = FeatureFlag("my_feature")
        result = flag.check(user_id=uuid.uuid4())
        assert result is True
        mock_redis.sismember.assert_not_called()


# -- Per-user canary ----------------------------------------------------------


class TestFeatureFlagPerUserCanary:

    def test_user_in_canary_set_enabled(self, mock_redis):
        from core.feature_flags.client import FeatureFlag

        mock_redis.get.return_value = None
        mock_redis.sismember.return_value = True
        flag = FeatureFlag("canary_flag")
        assert flag.check(user_id=uuid.uuid4()) is True

    def test_user_not_in_canary_set_disabled(self, mock_redis):
        from core.feature_flags.client import FeatureFlag

        mock_redis.get.return_value = None
        mock_redis.sismember.return_value = False
        flag = FeatureFlag("canary_flag")
        assert flag.check(user_id=uuid.uuid4()) is False

    def test_no_user_id_skips_canary_check(self, mock_redis):
        from core.feature_flags.client import FeatureFlag

        mock_redis.get.return_value = None
        flag = FeatureFlag("canary_flag")
        flag.check(user_id=None)
        mock_redis.sismember.assert_not_called()

    def test_add_user_calls_sadd(self, mock_redis):
        from core.feature_flags.client import FeatureFlag

        flag = FeatureFlag("canary_flag")
        user_id = uuid.uuid4()
        flag.add_user(user_id)
        mock_redis.sadd.assert_called_once()

    def test_remove_user_calls_srem(self, mock_redis):
        from core.feature_flags.client import FeatureFlag

        flag = FeatureFlag("canary_flag")
        user_id = uuid.uuid4()
        flag.remove_user(user_id)
        mock_redis.srem.assert_called_once()

    def test_user_id_as_string_works(self, mock_redis):
        from core.feature_flags.client import FeatureFlag

        mock_redis.sismember.return_value = True
        flag = FeatureFlag("canary_flag")
        assert flag.check(user_id="string-user-id") is True


# -- Percentage rollout -------------------------------------------------------


class TestFeatureFlagPercentageRollout:

    def test_100_percent_always_enabled(self, mock_redis):
        from core.feature_flags.client import FeatureFlag

        mock_redis.get.side_effect = lambda key: (
            b"100" if key.endswith(":pct") else None
        )
        mock_redis.sismember.return_value = False
        flag = FeatureFlag("pct_flag")
        assert flag.check(user_id=uuid.uuid4()) is True

    def test_0_percent_never_enabled(self, mock_redis):
        from core.feature_flags.client import FeatureFlag

        mock_redis.get.side_effect = lambda key: b"0" if key.endswith(":pct") else None
        mock_redis.sismember.return_value = False
        flag = FeatureFlag("pct_flag")
        assert flag.check(user_id=uuid.uuid4()) is False

    def test_same_user_always_same_result(self, mock_redis):
        """Deterministic: same user_id must get the same result every time."""
        from core.feature_flags.client import is_enabled

        mock_redis.get.side_effect = lambda key: b"50" if key.endswith(":pct") else None
        mock_redis.sismember.return_value = False
        user_id = uuid.uuid4()
        results = {is_enabled("stable_flag", user_id=user_id) for _ in range(20)}
        # Set has exactly 1 unique value - fully deterministic
        assert len(results) == 1

    def test_set_percentage_stores_value_in_redis(self, mock_redis):
        from core.feature_flags.client import FeatureFlag

        flag = FeatureFlag("pct_flag")
        flag.set_percentage(25)
        mock_redis.set.assert_called_once()
        call_args = str(mock_redis.set.call_args)
        assert "25" in call_args

    def test_percentage_clamped_at_100(self, mock_redis):
        from core.feature_flags.client import FeatureFlag

        flag = FeatureFlag("pct_flag")
        flag.set_percentage(999)
        call_args = str(mock_redis.set.call_args)
        assert "100" in call_args

    def test_percentage_clamped_at_0(self, mock_redis):
        from core.feature_flags.client import FeatureFlag

        flag = FeatureFlag("pct_flag")
        flag.set_percentage(-50)
        call_args = str(mock_redis.set.call_args)
        assert "0" in call_args

    def test_no_user_id_skips_percentage_check(self, mock_redis):
        """Without a user_id we cannot assign a bucket - return False."""
        from core.feature_flags.client import is_enabled

        mock_redis.get.side_effect = lambda key: (
            b"100" if key.endswith(":pct") else None
        )
        mock_redis.sismember.return_value = False
        result = is_enabled("pct_flag", user_id=None)
        assert result is False


# -- Status -------------------------------------------------------------------


class TestFeatureFlagStatus:

    def test_status_returns_all_required_keys(self, mock_redis):
        from core.feature_flags.client import FeatureFlag

        mock_redis.get.return_value = None
        mock_redis.scard.return_value = 5
        flag = FeatureFlag("status_flag")
        status = flag.status()
        assert "name" in status
        assert "global" in status
        assert "percentage" in status
        assert "user_count" in status

    def test_status_name_matches(self, mock_redis):
        from core.feature_flags.client import FeatureFlag

        flag = FeatureFlag("my_unique_flag")
        assert flag.status()["name"] == "my_unique_flag"

    def test_status_user_count_from_redis(self, mock_redis):
        from core.feature_flags.client import FeatureFlag

        mock_redis.scard.return_value = 42
        flag = FeatureFlag("flag")
        assert flag.status()["user_count"] == 42


# -- Redis failure resilience -------------------------------------------------


class TestFeatureFlagRedisFailure:

    def test_returns_false_on_connection_error(self):
        """Must fail safe - return False, never raise."""
        from core.feature_flags.client import is_enabled

        with patch(
            "core.feature_flags.client._get_redis",
            side_effect=ConnectionError("Redis down"),
        ):
            result = is_enabled("any_flag", user_id=uuid.uuid4())
        assert result is False

    def test_no_exception_bubbles_up(self):
        """Application code must never have to wrap is_enabled in try/except."""
        from core.feature_flags.client import is_enabled

        with patch(
            "core.feature_flags.client._get_redis",
            side_effect=Exception("Unexpected error"),
        ):
            # Must not raise
            is_enabled("any_flag")

    def test_flag_object_check_also_safe(self):
        from core.feature_flags.client import FeatureFlag

        with patch(
            "core.feature_flags.client._get_redis",
            side_effect=RuntimeError("Redis unavailable"),
        ):
            flag = FeatureFlag("safe_flag")
            result = flag.check(user_id=uuid.uuid4())
        assert result is False


# -- is_enabled helper --------------------------------------------------------


class TestIsEnabledHelper:

    def test_globally_enabled(self, mock_redis):
        from core.feature_flags.client import is_enabled

        mock_redis.get.return_value = b"1"
        assert is_enabled("global_flag") is True

    def test_globally_disabled(self, mock_redis):
        from core.feature_flags.client import is_enabled

        mock_redis.get.return_value = None
        assert is_enabled("global_flag") is False

    def test_per_user_via_canary(self, mock_redis):
        from core.feature_flags.client import is_enabled

        mock_redis.get.return_value = None
        mock_redis.sismember.return_value = True
        assert is_enabled("flag", user_id=uuid.uuid4()) is True

    def test_accepts_uuid_or_string(self, mock_redis):
        from core.feature_flags.client import is_enabled

        mock_redis.sismember.return_value = True
        assert is_enabled("flag", user_id=uuid.uuid4()) is True
        assert is_enabled("flag", user_id="plain-string") is True
