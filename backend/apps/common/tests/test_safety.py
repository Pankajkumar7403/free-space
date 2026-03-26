"""
apps/common/tests/test_safety.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Tests for LGBTQ+ safety features:
  - Blocking propagation
  - Content filtering for blocks
  - Outing prevention (identity field visibility)
  - Crisis resource injection
  - Audit logging
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest

# -- is_blocked ---------------------------------------------------------------


@pytest.mark.django_db
class TestIsBlocked:

    def test_returns_false_when_no_block_exists(self, user_factory):
        from apps.common.safety.services import is_blocked

        user_a = user_factory()
        user_b = user_factory()
        with patch("apps.common.safety.services.RedisClient") as mock_rc:
            mock_redis = MagicMock()
            mock_redis.get.return_value = None
            mock_rc.get_instance.return_value = mock_redis
            result = is_blocked(viewer_id=user_a.id, target_id=user_b.id)
        assert result is False

    def test_returns_true_when_viewer_blocked_target(self, user_factory):
        from apps.common.safety.services import is_blocked
        from apps.users.models import BlockedUser

        user_a = user_factory()
        user_b = user_factory()
        BlockedUser.objects.create(blocker=user_a, blocked=user_b)
        with patch("apps.common.safety.services.RedisClient") as mock_rc:
            mock_redis = MagicMock()
            mock_redis.get.return_value = None
            mock_rc.get_instance.return_value = mock_redis
            result = is_blocked(viewer_id=user_a.id, target_id=user_b.id)
        assert result is True

    def test_returns_true_when_target_blocked_viewer(self, user_factory):
        """Reverse block: B blocked A, so A viewing B should still be blocked."""
        from apps.common.safety.services import is_blocked
        from apps.users.models import BlockedUser

        user_a = user_factory()
        user_b = user_factory()
        BlockedUser.objects.create(blocker=user_b, blocked=user_a)
        with patch("apps.common.safety.services.RedisClient") as mock_rc:
            mock_redis = MagicMock()
            mock_redis.get.return_value = None
            mock_rc.get_instance.return_value = mock_redis
            result = is_blocked(viewer_id=user_a.id, target_id=user_b.id)
        assert result is True

    def test_cache_hit_avoids_db_query(self, user_factory):
        from apps.common.safety.services import is_blocked

        user_a = user_factory()
        user_b = user_factory()
        with patch("apps.common.safety.services.RedisClient") as mock_rc:
            mock_redis = MagicMock()
            mock_redis.get.return_value = b"1"  # Cache hit
            mock_rc.get_instance.return_value = mock_redis
            result = is_blocked(viewer_id=user_a.id, target_id=user_b.id)
        assert result is True

    def test_unblocked_users_cache_hit(self, user_factory):
        from apps.common.safety.services import is_blocked

        user_a = user_factory()
        user_b = user_factory()
        with patch("apps.common.safety.services.RedisClient") as mock_rc:
            mock_redis = MagicMock()
            mock_redis.get.return_value = b"0"  # Cached: not blocked
            mock_rc.get_instance.return_value = mock_redis
            result = is_blocked(viewer_id=user_a.id, target_id=user_b.id)
        assert result is False


# -- filter_queryset_for_blocks -----------------------------------------------


@pytest.mark.django_db
class TestFilterQuerysetForBlocks:

    def test_excludes_blocked_user_posts(self, user_factory, post_factory):
        from apps.common.safety.services import filter_queryset_for_blocks
        from apps.posts.models import Post
        from apps.users.models import BlockedUser

        viewer = user_factory()
        blocked = user_factory()
        other = user_factory()

        BlockedUser.objects.create(blocker=viewer, blocked=blocked)
        post_factory(author=blocked)
        post_factory(author=other)

        qs = Post.objects.all()
        filtered = filter_queryset_for_blocks(qs, viewer_id=viewer.id)

        authors = set(filtered.values_list("author_id", flat=True))
        assert blocked.id not in authors
        assert other.id in authors

    def test_excludes_blocking_user_posts(self, user_factory, post_factory):
        """If B blocked viewer, viewer should not see B's posts either."""
        from apps.common.safety.services import filter_queryset_for_blocks
        from apps.posts.models import Post
        from apps.users.models import BlockedUser

        viewer = user_factory()
        blocker = user_factory()

        BlockedUser.objects.create(blocker=blocker, blocked=viewer)
        post_factory(author=blocker)

        qs = Post.objects.all()
        filtered = filter_queryset_for_blocks(qs, viewer_id=viewer.id)

        authors = set(filtered.values_list("author_id", flat=True))
        assert blocker.id not in authors

    def test_no_blocks_returns_full_queryset(self, user_factory, post_factory):
        from apps.common.safety.services import filter_queryset_for_blocks
        from apps.posts.models import Post

        viewer = user_factory()
        user_a = user_factory()
        user_b = user_factory()
        post_factory(author=user_a)
        post_factory(author=user_b)

        qs = Post.objects.filter(author__in=[user_a, user_b])
        filtered = filter_queryset_for_blocks(qs, viewer_id=viewer.id)
        assert filtered.count() == 2


# -- Outing prevention --------------------------------------------------------


@pytest.mark.django_db
class TestGetVisibleIdentityFields:

    def test_owner_sees_all_fields(self, user_factory):
        from apps.common.safety.constants import PRIVATE_IDENTITY_FIELDS
        from apps.common.safety.services import get_visible_identity_fields

        user = user_factory()
        visible = get_visible_identity_fields(
            profile_user_id=user.id, viewer_id=user.id
        )
        assert visible == PRIVATE_IDENTITY_FIELDS

    def test_unauthenticated_sees_nothing(self, user_factory):
        from apps.common.safety.services import get_visible_identity_fields

        user = user_factory()
        visible = get_visible_identity_fields(profile_user_id=user.id, viewer_id=None)
        assert visible == set()

    def test_non_follower_sees_nothing(self, user_factory):
        from apps.common.safety.services import get_visible_identity_fields

        user = user_factory()
        viewer = user_factory()
        visible = get_visible_identity_fields(
            profile_user_id=user.id, viewer_id=viewer.id
        )
        assert visible == set()

    def test_follower_sees_all_fields(self, user_factory):
        from apps.common.safety.constants import PRIVATE_IDENTITY_FIELDS
        from apps.common.safety.services import get_visible_identity_fields
        from apps.users.models import Follow

        user = user_factory()
        viewer = user_factory()
        Follow.objects.create(follower=viewer, following=user)
        visible = get_visible_identity_fields(
            profile_user_id=user.id, viewer_id=viewer.id
        )
        assert visible == PRIVATE_IDENTITY_FIELDS


# -- Identity audit logging ---------------------------------------------------


class TestLogIdentityView:

    def test_stores_view_in_redis(self):
        from apps.common.safety.services import log_identity_view

        mock_redis = MagicMock()
        with patch("apps.common.safety.services.RedisClient") as mock_rc:
            mock_rc.get_instance.return_value = mock_redis
            log_identity_view(
                viewer_id=uuid.uuid4(),
                profile_id=uuid.uuid4(),
            )
        mock_redis.setex.assert_called_once()

    def test_ttl_is_seven_days(self):
        from apps.common.safety.constants import IDENTITY_VIEW_AUDIT_TTL
        from apps.common.safety.services import log_identity_view

        mock_redis = MagicMock()
        with patch("apps.common.safety.services.RedisClient") as mock_rc:
            mock_rc.get_instance.return_value = mock_redis
            log_identity_view(
                viewer_id=uuid.uuid4(),
                profile_id=uuid.uuid4(),
            )
        call_args = mock_redis.setex.call_args
        ttl = call_args[0][1]
        assert ttl == IDENTITY_VIEW_AUDIT_TTL

    def test_key_contains_both_user_ids(self):
        from apps.common.safety.services import log_identity_view

        viewer_id = uuid.uuid4()
        profile_id = uuid.uuid4()
        mock_redis = MagicMock()
        with patch("apps.common.safety.services.RedisClient") as mock_rc:
            mock_rc.get_instance.return_value = mock_redis
            log_identity_view(viewer_id=viewer_id, profile_id=profile_id)
        key = mock_redis.setex.call_args[0][0]
        assert str(viewer_id) in key
        assert str(profile_id) in key


# -- Crisis resources ---------------------------------------------------------


class TestGetCrisisResourcesForRequest:

    def test_returns_dict(self):
        from django.test import RequestFactory

        from apps.common.safety.services import get_crisis_resources_for_request

        request = RequestFactory().get("/")
        result = get_crisis_resources_for_request(request)
        assert isinstance(result, dict)

    def test_returns_something_for_unknown_locale(self):
        from django.test import RequestFactory

        from apps.common.safety.services import get_crisis_resources_for_request

        request = RequestFactory().get("/")
        request.META["HTTP_ACCEPT_LANGUAGE"] = "xx-XX"
        result = get_crisis_resources_for_request(request)
        assert result is not None


# -- Crisis resource middleware -----------------------------------------------


class TestCrisisResourceMiddleware:

    def test_adds_header_when_crisis_detected(self):
        from django.http import HttpRequest, HttpResponse

        from apps.common.safety.middleware import CrisisResourceMiddleware

        response = HttpResponse("ok")
        middleware = CrisisResourceMiddleware(get_response=lambda r: response)
        request = HttpRequest()
        request._crisis_content_detected = True
        resp = middleware(request)
        assert resp["X-Crisis-Resources"] == "true"

    def test_no_header_when_no_crisis(self):
        from django.http import HttpRequest, HttpResponse

        from apps.common.safety.middleware import CrisisResourceMiddleware

        response = HttpResponse("ok")
        middleware = CrisisResourceMiddleware(get_response=lambda r: response)
        request = HttpRequest()
        resp = middleware(request)
        assert "X-Crisis-Resources" not in resp
