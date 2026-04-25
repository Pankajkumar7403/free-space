# Qommunity MVP Simplification — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove overengineered infrastructure (Kafka, Redis, WebSockets, Prometheus, Elasticsearch, feature flags) and replace with direct DB queries, synchronous service calls, and polling — without rebuilding from scratch.

**Architecture:** Four phases — (1) delete dead infrastructure files, (2) simplify backend behavior (feed, likes, notifications), (3) add Report model + endpoint, (4) simplify frontend. Phases 1-3 are sequential; Phase 4 is independent and can be worked in parallel.

**Tech Stack:** Django 4.x, DRF, PostgreSQL, Celery (media only), pytest, Next.js 14, Turborepo, pnpm, Zustand, TanStack Query

---

## File Map

### Backend — Delete
```
core/kafka/                              # 4 files
core/feature_flags/                      # 2 files
core/monitoring/prometheus.py
core/middleware/metrics.py
core/pagination/connection.py
core/security/app_version.py
core/redis/                              # client.py, cache.py, rate_limit.py
core/test/test_kafka_prouducer.py
core/test/test_redis_client.py
core/test/test_rate_limiter.py
core/tests/test_feature_flags.py
core/tests/test_metrics.py
apps/feed/fanout.py
apps/feed/cache.py
apps/feed/ranking.py
apps/feed/management/
apps/feed/tests/test_fanout.py
apps/feed/tests/test_cache.py
apps/feed/tests/test_ranking.py
apps/feed/tests/test_tasks.py
apps/notifications/consumers.py
apps/notifications/dispatchers.py
apps/notifications/management/
apps/notifications/tests/test_consumers.py
apps/notifications/tests/test_event_contracts.py
apps/comments/tests/test_events.py
apps/common/gdpr/                        # 6 files
apps/common/moderation/image_classifier.py
apps/common/moderation/tasks.py
apps/common/tests/test_gdpr.py
apps/likes/cache.py
apps/likes/tests/test_cache.py
tests/load/
config/routing.py
apps/comments/events.py
apps/feed/events.py
apps/likes/events.py
apps/media/events.py
apps/notifications/events.py
apps/posts/events.py
apps/users/events.py
apps/common/events.py
apps/comments/tasks.py
apps/feed/tasks.py
apps/likes/tasks.py
apps/notifications/tasks.py
apps/posts/tasks.py
apps/users/tasks.py
apps/common/tasks.py
```

### Backend — Modify
```
config/asgi.py                           # plain Django ASGI, no Channels
config/urls.py                           # remove prometheus + gdpr urls, add reports
config/settings/base.py                  # remove dead apps/middleware, add CELERY_BROKER_URL
core/pagination/cursor.py                # remove FeedCursorPagination class
apps/common/views.py                     # remove _check_redis(), simplify health check
apps/common/moderation/services.py      # remove moderate_image_async, Prometheus import
apps/feed/selectors.py                   # rewrite: return QuerySet, remove Redis paths
apps/feed/services.py                    # remove push_post_to_explore/on_user_login/on_user_unfollow
apps/feed/views.py                       # use CursorPagination, remove FeedPage references
apps/likes/services.py                   # remove Redis calls, add direct notification
apps/comments/services.py               # remove Kafka event, add direct notification
apps/users/services.py                   # remove emit_user_followed, add direct notifications
apps/common/models.py                    # add Report model
apps/common/serializers.py              # add ReportSerializer
apps/common/urls.py                      # add /reports/ url
```

### Backend — Create
```
apps/common/migrations/000X_add_report.py  # via makemigrations
apps/feed/tests/test_selectors.py
apps/common/tests/test_reports.py
```

### Frontend — Delete
```
packages/hooks/                          # after contents moved to web app
packages/validators/                     # after contents moved to web app
packages/ui-kit/                         # after contents moved to web app
apps/web/src/app/api/users/             # duplicate of api/auth/
apps/web/src/app/(main)/explore/trending/page.tsx
apps/web/src/app/(main)/hashtag/[tag]/page.tsx
```

### Frontend — Move
```
packages/hooks/src/*.ts       → apps/web/src/hooks/
packages/validators/src/*.ts  → apps/web/src/lib/validators/
packages/ui-kit/src/components/*.tsx  → apps/web/src/components/ui/
packages/ui-kit/src/primitives/*.tsx  → apps/web/src/components/ui/
packages/ui-kit/src/tokens/*.ts       → apps/web/src/lib/tokens/
```

### Frontend — Modify
```
apps/web/src/lib/env.ts                  # remove NEXT_PUBLIC_WS_URL
packages/types/src/notification.ts       # remove NotificationEvent interface
apps/web/package.json                    # remove @qommunity/hooks, validators, ui-kit deps
pnpm-workspace.yaml                      # remove deleted packages from workspace
```

### Frontend — Create
```
apps/web/src/app/(main)/notifications/page.tsx
```

---

## Phase 1: Infrastructure Deletion

### Task 1: Delete core infrastructure + associated tests

**Files:**
- Delete: `core/kafka/` (entire directory)
- Delete: `core/feature_flags/` (entire directory)
- Delete: `core/monitoring/prometheus.py`
- Delete: `core/middleware/metrics.py`
- Delete: `core/pagination/connection.py`
- Delete: `core/security/app_version.py`
- Delete: `core/redis/` (entire directory)
- Delete: `core/test/test_kafka_prouducer.py`
- Delete: `core/test/test_redis_client.py`
- Delete: `core/test/test_rate_limiter.py`
- Delete: `core/tests/test_feature_flags.py`
- Delete: `core/tests/test_metrics.py`

- [ ] **Step 1: Delete all files**

```bash
cd backend
rm -rf core/kafka core/feature_flags core/redis
rm core/monitoring/prometheus.py
rm core/middleware/metrics.py
rm core/pagination/connection.py
rm core/security/app_version.py
rm core/test/test_kafka_prouducer.py core/test/test_redis_client.py core/test/test_rate_limiter.py
rm core/tests/test_feature_flags.py core/tests/test_metrics.py
```

- [ ] **Step 2: Verify no remaining imports from deleted modules**

```bash
cd backend
grep -r "from core.kafka" . --include="*.py" | grep -v ".pyc"
grep -r "from core.redis" . --include="*.py" | grep -v ".pyc"
grep -r "from core.feature_flags" . --include="*.py" | grep -v ".pyc"
grep -r "from core.monitoring.prometheus" . --include="*.py" | grep -v ".pyc"
grep -r "from core.middleware.metrics" . --include="*.py" | grep -v ".pyc"
grep -r "from core.pagination.connection" . --include="*.py" | grep -v ".pyc"
grep -r "from core.security.app_version" . --include="*.py" | grep -v ".pyc"
```

Expected: each command returns empty output. Any remaining imports are call sites that must be fixed before this task is complete — grep the file, find the import, delete the line.

Note: `apps/common/views.py` imports `core.redis.client` in `_check_redis()` — this is fixed in Task 3.

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "chore: delete core infrastructure (kafka, redis, feature_flags, prometheus)"
```

---

### Task 2: Delete app-layer infrastructure + associated tests

**Files:**
- Delete: `apps/feed/fanout.py`, `cache.py`, `ranking.py`, `management/`
- Delete: `apps/feed/tests/test_fanout.py`, `test_cache.py`, `test_ranking.py`, `test_tasks.py`
- Delete: `apps/notifications/consumers.py`, `dispatchers.py`, `management/`
- Delete: `apps/notifications/tests/test_consumers.py`, `test_event_contracts.py`
- Delete: `apps/comments/tests/test_events.py`
- Delete: `apps/common/gdpr/` (entire directory)
- Delete: `apps/common/moderation/image_classifier.py`
- Delete: `apps/common/moderation/tasks.py`
- Delete: `apps/common/tests/test_gdpr.py`
- Delete: `apps/likes/cache.py`
- Delete: `apps/likes/tests/test_cache.py`
- Delete: `tests/load/` (entire directory)
- Delete: `config/routing.py`
- Delete: all `events.py` files (8 files)
- Delete: all non-media `tasks.py` files (7 files)

- [ ] **Step 1: Delete feed infrastructure**

```bash
cd backend
rm apps/feed/fanout.py apps/feed/cache.py apps/feed/ranking.py
rm -rf apps/feed/management
rm apps/feed/tests/test_fanout.py apps/feed/tests/test_cache.py
rm apps/feed/tests/test_ranking.py apps/feed/tests/test_tasks.py
```

- [ ] **Step 2: Delete notification infrastructure**

```bash
rm apps/notifications/consumers.py apps/notifications/dispatchers.py
rm -rf apps/notifications/management
rm apps/notifications/tests/test_consumers.py apps/notifications/tests/test_event_contracts.py
```

- [ ] **Step 3: Delete common infrastructure + moderation AI**

```bash
rm -rf apps/common/gdpr
rm apps/common/moderation/image_classifier.py apps/common/moderation/tasks.py
rm apps/common/tests/test_gdpr.py
rm apps/comments/tests/test_events.py
```

- [ ] **Step 4: Delete likes Redis cache + load tests + WebSocket routing**

```bash
rm apps/likes/cache.py apps/likes/tests/test_cache.py
rm -rf tests/load
rm config/routing.py
```

- [ ] **Step 5: Delete all events.py files**

```bash
rm apps/comments/events.py apps/feed/events.py apps/likes/events.py
rm apps/media/events.py apps/notifications/events.py apps/posts/events.py
rm apps/users/events.py apps/common/events.py
```

- [ ] **Step 6: Delete all non-media tasks.py files**

```bash
rm apps/comments/tasks.py apps/feed/tasks.py apps/likes/tasks.py
rm apps/notifications/tasks.py apps/posts/tasks.py apps/users/tasks.py
rm apps/common/tasks.py
```

Note: `apps/media/tasks.py` is intentionally kept — Celery remains for media processing only.

- [ ] **Step 7: Verify no remaining imports from deleted modules**

```bash
cd backend
grep -r "from apps.feed.fanout\|from apps.feed.cache\|from apps.feed.ranking" . --include="*.py"
grep -r "from apps.likes.cache" . --include="*.py"
grep -r "from apps.common.gdpr\|from apps.common.moderation.image_classifier\|from apps.common.moderation.tasks" . --include="*.py"
grep -r "\.events import\|from apps.*events" . --include="*.py"
grep -r "from apps.*tasks import\|\.tasks import" . --include="*.py" | grep -v "apps/media/tasks"
```

Expected: all empty. Fix any remaining imports found before proceeding.

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "chore: delete app-layer infrastructure (events, redis cache, gdpr, moderation AI, load tests)"
```

---

### Task 3: Simplify config, settings, health check

**Files:**
- Modify: `config/asgi.py`
- Modify: `config/urls.py`
- Modify: `config/settings/base.py`
- Modify: `apps/common/views.py`

- [ ] **Step 1: Simplify config/asgi.py**

Replace the entire file:

```python
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
application = get_asgi_application()
```

- [ ] **Step 2: Simplify apps/common/views.py — remove Redis check**

Replace the entire file:

```python
"""
Health check endpoint for Docker/K8s probes.
GET /api/v1/health/  ->  200 if database healthy, 503 if not.
"""
from __future__ import annotations

import logging
import time

from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []

    def get(self, request):
        db = _check_database()
        healthy = db["status"] == "ok"
        return Response(
            {"status": "healthy" if healthy else "degraded", "checks": {"database": db}},
            status=200 if healthy else 503,
        )


def _check_database() -> dict:
    start = time.perf_counter()
    try:
        from django.db import connection
        connection.ensure_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return {"status": "ok", "latency_ms": round((time.perf_counter() - start) * 1000, 2)}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}
```

- [ ] **Step 3: Simplify config/urls.py — remove prometheus + gdpr, add reports**

Replace the entire file:

```python
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from apps.common.views import HealthCheckView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/health/", HealthCheckView.as_view(), name="health-check"),
    # API v1
    path("api/v1/users/", include("apps.users.urls", namespace="users")),
    path("api/v1/posts/", include("apps.posts.urls", namespace="posts")),
    path("api/v1/comments/", include("apps.comments.urls", namespace="comments")),
    path("api/v1/posts/", include("apps.likes.urls", namespace="likes")),
    path("api/v1/media/", include("apps.media.urls", namespace="media")),
    path("api/v1/feed/", include("apps.feed.urls", namespace="feed")),
    path("api/v1/notifications/", include("apps.notifications.urls", namespace="notifications")),
    path("api/v1/reports/", include("apps.common.urls", namespace="common")),
    # OpenAPI schema + interactive docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
```

- [ ] **Step 4: Update config/settings/base.py — remove dead apps/middleware/settings**

Open `config/settings/base.py` and make these changes:

**In `THIRD_PARTY_APPS`, remove:**
```python
"django_prometheus",
"channels",
"django_elasticsearch_dsl",
"django_celery_beat",
```

**In `INSTALLED_APPS`, remove:**
```python
"daphne",
```
(The `["daphne"] +` prefix at the top of INSTALLED_APPS — remove this entirely.)

**In `MIDDLEWARE`, remove these two lines:**
```python
"django_prometheus.middleware.PrometheusBeforeMiddleware",
"core.middleware.metrics.PrometheusMetricsMiddleware",
```

**Add after the existing Celery settings** (find `CELERY_` block and add):
```python
CELERY_BROKER_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
```

**Remove any settings blocks for:** `KAFKA_*`, `ELASTICSEARCH_*`, `CHANNEL_LAYERS`, `PROMETHEUS_*`.

- [ ] **Step 5: Verify Django system check passes**

```bash
cd backend
python manage.py check
```

Expected output: `System check identified no issues (0 silenced).`

If there are errors, read the error message and fix the missing import or setting before continuing.

- [ ] **Step 6: Remove FeedCursorPagination from core/pagination/cursor.py**

Open `core/pagination/cursor.py` and delete the `FeedCursorPagination` class (lines 93-101):

```python
# DELETE this entire class:
class FeedCursorPagination(CursorPagination):
    """
    Feed-specific paginator.

    The feed is ordered by score (ranking), not created_at, so we use
    a composite cursor of (score DESC, id ASC) for stable ordering.
    """

    ordering = "-score"
    page_size = 20
```

The file should now only contain `CursorPagination`.

- [ ] **Step 7: Run the full test suite**

```bash
cd backend
python -m pytest --tb=short -q
```

Expected: all remaining tests pass. If a test imports a deleted module, delete that test file (it tests deleted code). If a non-deleted test fails, fix the underlying issue.

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "chore: simplify config, settings, health check — remove Channels/Prometheus/Elasticsearch"
```

---

## Phase 2: Backend Behavior Changes

### Task 4: Simplify likes services — remove Redis, add direct notification

**Files:**
- Modify: `apps/likes/services.py`
- Test: `apps/likes/tests/test_services.py`

The current `like_object()` function has three responsibilities we're changing:
1. Remove the Redis membership check (use DB `unique_together` as the only duplicate guard)
2. Remove the Redis counter increment (`like_incr`)
3. Replace the Kafka event (`emit_like_created`) with a direct `create_notification()` call

`get_like_count()` currently falls back to DB on Redis miss — simplify to DB only.
`is_liked_by()` currently checks Redis — simplify to DB query.

- [ ] **Step 1: Write the failing tests**

Add to `apps/likes/tests/test_services.py`:

```python
from unittest.mock import patch, call
import pytest
from apps.likes.services import like_object, unlike_object, get_like_count, is_liked_by
from apps.likes.exceptions import AlreadyLikedError, NotLikedError


@pytest.mark.django_db
def test_like_post_creates_notification(user_factory, post_factory):
    """Liking a post fires a notification to the post author."""
    author = user_factory()
    liker = user_factory()
    post = post_factory(author=author)

    with patch("apps.likes.services.create_notification") as mock_notify:
        like_object(user=liker, obj=post)
        mock_notify.assert_called_once()
        kwargs = mock_notify.call_args.kwargs
        assert kwargs["recipient_id"] == author.pk
        assert kwargs["actor_id"] == liker.pk


@pytest.mark.django_db
def test_like_post_no_self_notification(user_factory, post_factory):
    """Liking your own post does not create a notification."""
    user = user_factory()
    post = post_factory(author=user)

    with patch("apps.likes.services.create_notification") as mock_notify:
        like_object(user=user, obj=post)
        mock_notify.assert_not_called()


@pytest.mark.django_db
def test_like_post_duplicate_raises(user_factory, post_factory):
    """Liking the same post twice raises AlreadyLikedError."""
    user = user_factory()
    post = post_factory()
    like_object(user=user, obj=post)
    with pytest.raises(AlreadyLikedError):
        like_object(user=user, obj=post)


@pytest.mark.django_db
def test_get_like_count_from_db(user_factory, post_factory):
    """get_like_count returns DB count, no Redis."""
    liker1 = user_factory()
    liker2 = user_factory()
    post = post_factory()
    like_object(user=liker1, obj=post)
    like_object(user=liker2, obj=post)
    assert get_like_count(obj=post) == 2


@pytest.mark.django_db
def test_is_liked_by_db(user_factory, post_factory):
    """is_liked_by uses DB, not Redis."""
    user = user_factory()
    post = post_factory()
    assert is_liked_by(user=user, obj=post) is False
    like_object(user=user, obj=post)
    assert is_liked_by(user=user, obj=post) is True
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd backend
python -m pytest apps/likes/tests/test_services.py -v -k "test_like_post_creates_notification or test_like_post_no_self_notification or test_like_post_duplicate_raises or test_get_like_count_from_db or test_is_liked_by_db"
```

Expected: tests fail (imports will error because `apps/likes/services.py` still references deleted modules).

- [ ] **Step 3: Rewrite apps/likes/services.py**

Replace the entire file:

```python
from __future__ import annotations

import logging

from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from apps.likes.constants import CT_COMMENT, CT_POST
from apps.likes.exceptions import AlreadyLikedError, LikeTargetNotFoundError, NotLikedError
from apps.likes.models import Like
from apps.users.models import User

logger = logging.getLogger(__name__)


def _resolve_content_type(obj) -> tuple[ContentType, str]:
    """Return (ContentType instance, short label) for a Post or Comment."""
    from apps.comments.models import Comment
    from apps.posts.models import Post

    if isinstance(obj, Post):
        return ContentType.objects.get_for_model(Post), CT_POST
    if isinstance(obj, Comment):
        return ContentType.objects.get_for_model(Comment), CT_COMMENT
    raise LikeTargetNotFoundError(
        message=f"Cannot like object of type {type(obj).__name__}"
    )


@transaction.atomic
def like_object(*, user: User, obj) -> Like:
    """
    Like a Post or Comment.
    DB unique_together is the duplicate guard.
    Fires a notification to the content author (skipped for self-likes).
    """
    from apps.notifications.constants import NotificationType
    from apps.notifications.services import create_notification

    ct, ct_label = _resolve_content_type(obj)

    try:
        like = Like.objects.create(user=user, content_type=ct, object_id=obj.pk)
    except Exception:
        raise AlreadyLikedError()

    author = getattr(obj, "author", None)
    if author is not None and author.pk != user.pk:
        content_type_label = "posts.Post" if ct_label == CT_POST else "comments.Comment"
        notification_type = (
            str(NotificationType.LIKE_POST) if ct_label == CT_POST
            else str(NotificationType.LIKE_COMMENT)
        )
        create_notification(
            recipient_id=author.pk,
            actor_id=user.pk,
            notification_type=notification_type,
            target_id=obj.pk,
            target_content_type_label=content_type_label,
        )

    return like


@transaction.atomic
def unlike_object(*, user: User, obj) -> None:
    """Unlike a Post or Comment. Raises NotLikedError if not previously liked."""
    ct, _ = _resolve_content_type(obj)
    deleted, _ = Like.objects.filter(user=user, content_type=ct, object_id=obj.pk).delete()
    if not deleted:
        raise NotLikedError()


def get_like_count(*, obj) -> int:
    """Return the like count for an object, directly from DB."""
    ct, _ = _resolve_content_type(obj)
    return Like.objects.filter(content_type=ct, object_id=obj.pk).count()


def is_liked_by(*, user: User, obj) -> bool:
    """Check whether a user has liked an object, directly from DB."""
    ct, _ = _resolve_content_type(obj)
    return Like.objects.filter(user=user, content_type=ct, object_id=obj.pk).exists()
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
cd backend
python -m pytest apps/likes/tests/test_services.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add apps/likes/services.py apps/likes/tests/test_services.py
git commit -m "refactor(likes): remove Redis cache, add direct notification on like"
```

---

### Task 5: Wire notification in comments services

**Files:**
- Modify: `apps/comments/services.py`
- Test: `apps/comments/tests/test_services.py`

Replace the `emit_comment_created(comment=comment)` Kafka call with direct `create_notification()` calls for both the post author (new comment) and the parent comment author (reply).

- [ ] **Step 1: Write the failing tests**

Add to `apps/comments/tests/test_services.py`:

```python
from unittest.mock import patch
import pytest
from apps.comments.services import CreateCommentInput, create_comment


@pytest.mark.django_db
def test_comment_notifies_post_author(user_factory, post_factory):
    """Commenting on a post notifies the post author."""
    author = user_factory()
    commenter = user_factory()
    post = post_factory(author=author, allow_comments=True)

    with patch("apps.comments.services.create_notification") as mock_notify:
        create_comment(CreateCommentInput(
            post_id=post.pk, author_id=commenter.pk, content="Nice post!"
        ))
        mock_notify.assert_called_once()
        assert mock_notify.call_args.kwargs["recipient_id"] == author.pk
        assert mock_notify.call_args.kwargs["actor_id"] == commenter.pk


@pytest.mark.django_db
def test_comment_no_self_notification(user_factory, post_factory):
    """Commenting on your own post does not notify yourself."""
    user = user_factory()
    post = post_factory(author=user, allow_comments=True)

    with patch("apps.comments.services.create_notification") as mock_notify:
        create_comment(CreateCommentInput(
            post_id=post.pk, author_id=user.pk, content="My own post!"
        ))
        mock_notify.assert_not_called()


@pytest.mark.django_db
def test_reply_notifies_parent_comment_author(user_factory, post_factory, comment_factory):
    """Replying to a comment notifies both post author and parent comment author."""
    post_author = user_factory()
    commenter = user_factory()
    replier = user_factory()
    post = post_factory(author=post_author, allow_comments=True)
    parent = comment_factory(post=post, author=commenter)

    with patch("apps.comments.services.create_notification") as mock_notify:
        create_comment(CreateCommentInput(
            post_id=post.pk, author_id=replier.pk,
            content="Nice comment!", parent_id=parent.pk,
        ))
        recipient_ids = {call.kwargs["recipient_id"] for call in mock_notify.call_args_list}
        assert post_author.pk in recipient_ids
        assert commenter.pk in recipient_ids
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd backend
python -m pytest apps/comments/tests/test_services.py -v -k "test_comment_notifies or test_reply_notifies or test_comment_no_self"
```

Expected: tests fail.

- [ ] **Step 3: Update apps/comments/services.py**

Replace the import block at the top of the file (remove `emit_comment_created`):

```python
# Remove this line:
from apps.comments.events import emit_comment_created
```

Replace the `emit_comment_created(comment=comment)` call at the end of `create_comment()` with:

```python
    # Notify post author about new comment (skip self-comments)
    from apps.notifications.constants import NotificationType
    from apps.notifications.services import create_notification

    if str(comment.author_id) != str(post.author_id):
        create_notification(
            recipient_id=post.author.pk,
            actor_id=comment.author_id,
            notification_type=str(NotificationType.COMMENT),
            target_id=comment.pk,
            target_content_type_label="comments.Comment",
        )

    # Notify parent comment author about reply (skip duplicate if same as post author)
    if (
        parent is not None
        and str(parent.author_id) != str(comment.author_id)
        and str(parent.author_id) != str(post.author_id)
    ):
        create_notification(
            recipient_id=parent.author_id,
            actor_id=comment.author_id,
            notification_type=str(NotificationType.COMMENT_REPLY),
            target_id=comment.pk,
            target_content_type_label="comments.Comment",
        )
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
cd backend
python -m pytest apps/comments/tests/test_services.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add apps/comments/services.py apps/comments/tests/test_services.py
git commit -m "refactor(comments): replace Kafka event with direct notification call"
```

---

### Task 6: Wire notification in users services — follow + accept

**Files:**
- Modify: `apps/users/services.py`
- Test: `apps/users/tests/test_services.py`

Two places emit `emit_user_followed` — both replaced with `create_notification()`:
1. `follow_user()` — only when the follow is newly created AND status is ACCEPTED
2. `accept_follow_request()` — always (accepting a pending request always warrants a notification)

- [ ] **Step 1: Write the failing tests**

Add to `apps/users/tests/test_services.py`:

```python
from unittest.mock import patch
import pytest
from apps.users.services import follow_user, accept_follow_request


@pytest.mark.django_db
def test_follow_public_user_fires_notification(user_factory):
    """Following a public user creates a follow notification."""
    follower = user_factory()
    following = user_factory()  # public by default

    with patch("apps.users.services.create_notification") as mock_notify:
        follow_user(follower_id=follower.pk, following_id=following.pk)
        mock_notify.assert_called_once()
        assert mock_notify.call_args.kwargs["recipient_id"] == following.pk
        assert mock_notify.call_args.kwargs["actor_id"] == follower.pk


@pytest.mark.django_db
def test_follow_private_user_no_notification(user_factory, private_user_factory):
    """Following a private user (pending status) does NOT create a notification."""
    follower = user_factory()
    following = private_user_factory()

    with patch("apps.users.services.create_notification") as mock_notify:
        follow_user(follower_id=follower.pk, following_id=following.pk)
        mock_notify.assert_not_called()


@pytest.mark.django_db
def test_accept_follow_request_fires_notification(user_factory, private_user_factory):
    """Accepting a follow request fires a follow notification."""
    follower = user_factory()
    following = private_user_factory()
    follow_user(follower_id=follower.pk, following_id=following.pk)

    with patch("apps.users.services.create_notification") as mock_notify:
        accept_follow_request(user_id=following.pk, follower_id=follower.pk)
        mock_notify.assert_called_once()
        assert mock_notify.call_args.kwargs["recipient_id"] == following.pk
        assert mock_notify.call_args.kwargs["actor_id"] == follower.pk


@pytest.mark.django_db
def test_refollow_does_not_double_notify(user_factory):
    """Re-following after unfollow does not create a duplicate notification."""
    from apps.users.services import unfollow_user
    follower = user_factory()
    following = user_factory()
    follow_user(follower_id=follower.pk, following_id=following.pk)
    unfollow_user(follower_id=follower.pk, following_id=following.pk)

    with patch("apps.users.services.create_notification") as mock_notify:
        follow_user(follower_id=follower.pk, following_id=following.pk)
        mock_notify.assert_called_once()
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd backend
python -m pytest apps/users/tests/test_services.py -v -k "test_follow or test_accept_follow or test_refollow"
```

Expected: tests fail.

- [ ] **Step 3: Update apps/users/services.py**

**Remove** the import at the top:
```python
from apps.users.events import emit_user_followed
```

**In `follow_user()`**, replace the `emit_user_followed` call with a direct notification.

Find and replace this block (around line 477):
```python
    follow, _ = Follow.objects.get_or_create(
        follower=follower,
        following=following,
        defaults={"status": status},
    )
    if follow.status == FollowStatusChoices.ACCEPTED:
        emit_user_followed(follower_id=str(follower.pk), following_id=str(following.pk))
    return follow
```

With:
```python
    from apps.notifications.constants import NotificationType
    from apps.notifications.services import create_notification

    follow, created = Follow.objects.get_or_create(
        follower=follower,
        following=following,
        defaults={"status": status},
    )
    if created and follow.status == FollowStatusChoices.ACCEPTED:
        create_notification(
            recipient_id=following.pk,
            actor_id=follower.pk,
            notification_type=str(NotificationType.FOLLOW),
            target_id=None,
            target_content_type_label=None,
        )
    return follow
```

**In `accept_follow_request()`**, replace the `emit_user_followed` call:

Find:
```python
    follow.status = FollowStatusChoices.ACCEPTED
    follow.save(update_fields=["status", "updated_at"])
    emit_user_followed(follower_id=str(follower_id), following_id=str(user_id))
    return follow
```

With:
```python
    from apps.notifications.constants import NotificationType
    from apps.notifications.services import create_notification

    follow.status = FollowStatusChoices.ACCEPTED
    follow.save(update_fields=["status", "updated_at"])
    create_notification(
        recipient_id=follow.following_id,
        actor_id=follow.follower_id,
        notification_type=str(NotificationType.FOLLOW),
        target_id=None,
        target_content_type_label=None,
    )
    return follow
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
cd backend
python -m pytest apps/users/tests/test_services.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add apps/users/services.py apps/users/tests/test_services.py
git commit -m "refactor(users): replace emit_user_followed with direct notification call"
```

---

### Task 7: Rewrite feed selector + simplify feed views and services

**Files:**
- Modify: `apps/feed/selectors.py` (full rewrite)
- Modify: `apps/feed/services.py` (remove dead functions)
- Modify: `apps/feed/views.py` (use CursorPagination)
- Create: `apps/feed/tests/test_selectors.py`

- [ ] **Step 1: Write the failing tests**

Create `apps/feed/tests/test_selectors.py`:

```python
import pytest
from apps.feed.selectors import get_user_feed, get_explore_feed
from apps.posts.constants import PostVisibility, PostStatus


@pytest.mark.django_db
def test_feed_includes_own_posts(user_factory, post_factory):
    """User's own posts appear in their feed regardless of visibility."""
    user = user_factory()
    own_public = post_factory(author=user, visibility=PostVisibility.PUBLIC)
    own_private = post_factory(author=user, visibility=PostVisibility.PRIVATE)

    qs = get_user_feed(user=user)
    ids = list(qs.values_list("pk", flat=True))
    assert own_public.pk in ids
    assert own_private.pk in ids


@pytest.mark.django_db
def test_feed_includes_followed_users_public_and_followers_only(
    user_factory, post_factory, follow_factory
):
    """Followed user's PUBLIC and FOLLOWERS_ONLY posts appear in feed."""
    user = user_factory()
    followed = user_factory()
    follow_factory(follower=user, following=followed, status="accepted")

    pub = post_factory(author=followed, visibility=PostVisibility.PUBLIC)
    fol = post_factory(author=followed, visibility=PostVisibility.FOLLOWERS_ONLY)
    prv = post_factory(author=followed, visibility=PostVisibility.PRIVATE)

    qs = get_user_feed(user=user)
    ids = list(qs.values_list("pk", flat=True))
    assert pub.pk in ids
    assert fol.pk in ids
    assert prv.pk not in ids   # PRIVATE from others excluded


@pytest.mark.django_db
def test_feed_excludes_non_followed_posts(user_factory, post_factory):
    """Posts from users not followed do not appear in feed."""
    user = user_factory()
    stranger = user_factory()
    stranger_post = post_factory(author=stranger, visibility=PostVisibility.PUBLIC)

    qs = get_user_feed(user=user)
    ids = list(qs.values_list("pk", flat=True))
    assert stranger_post.pk not in ids


@pytest.mark.django_db
def test_feed_excludes_blocked_user_posts(user_factory, post_factory, follow_factory, block_factory):
    """Posts from blocked users are excluded even if followed."""
    user = user_factory()
    blocked = user_factory()
    follow_factory(follower=user, following=blocked, status="accepted")
    block_factory(blocker=user, blocked=blocked)
    post = post_factory(author=blocked, visibility=PostVisibility.PUBLIC)

    qs = get_user_feed(user=user)
    ids = list(qs.values_list("pk", flat=True))
    assert post.pk not in ids


@pytest.mark.django_db
def test_feed_ordered_newest_first(user_factory, post_factory):
    """Feed posts are ordered by created_at descending."""
    user = user_factory()
    older = post_factory(author=user, visibility=PostVisibility.PUBLIC)
    newer = post_factory(author=user, visibility=PostVisibility.PUBLIC)

    qs = get_user_feed(user=user)
    pks = list(qs.values_list("pk", flat=True))
    assert pks.index(newer.pk) < pks.index(older.pk)


@pytest.mark.django_db
def test_explore_excludes_followed_and_own(user_factory, post_factory, follow_factory):
    """Explore feed excludes own posts and posts from followed users."""
    user = user_factory()
    followed = user_factory()
    stranger = user_factory()
    follow_factory(follower=user, following=followed, status="accepted")

    own_post = post_factory(author=user, visibility=PostVisibility.PUBLIC)
    followed_post = post_factory(author=followed, visibility=PostVisibility.PUBLIC)
    discover_post = post_factory(author=stranger, visibility=PostVisibility.PUBLIC)

    qs = get_explore_feed(user=user)
    ids = list(qs.values_list("pk", flat=True))
    assert own_post.pk not in ids
    assert followed_post.pk not in ids
    assert discover_post.pk in ids
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd backend
python -m pytest apps/feed/tests/test_selectors.py -v
```

Expected: tests fail (selector uses deleted Redis modules).

- [ ] **Step 3: Rewrite apps/feed/selectors.py**

Replace the entire file:

```python
from __future__ import annotations

from django.db.models import Q, QuerySet

from apps.posts.constants import PostStatus, PostVisibility
from apps.posts.models import Post
from apps.users.models import Follow
from apps.users.selectors import get_blocked_users


def get_user_feed(*, user) -> QuerySet:
    """
    Home feed: own posts + followed users' posts, newest first.
    Visibility rules:
      - Own posts: all visibility levels (including PRIVATE)
      - Others' posts: PUBLIC, FOLLOWERS_ONLY, CLOSE_FRIENDS (never PRIVATE)
    Pagination is applied by the view using CursorPagination.
    """
    blocked_ids = get_blocked_users(user).values_list("pk", flat=True)

    following_qs = Follow.objects.filter(
        follower=user, status="accepted"
    ).values("following_id")

    own_posts = Q(author=user)

    followed_posts = Q(
        author_id__in=following_qs,
        visibility__in=[
            PostVisibility.PUBLIC,
            PostVisibility.FOLLOWERS_ONLY,
            PostVisibility.CLOSE_FRIENDS,
        ],
    )

    return (
        Post.objects.filter(
            (own_posts | followed_posts),
            status=PostStatus.PUBLISHED,
            is_deleted=False,
        )
        .exclude(author_id__in=blocked_ids)
        .select_related("author")
        .prefetch_related("media", "hashtags")
        .order_by("-created_at")
    )


def get_explore_feed(*, user) -> QuerySet:
    """
    Explore feed: public posts from users the requester doesn't follow.
    Excludes own posts and posts from blocked users.
    Pagination is applied by the view using CursorPagination.
    """
    blocked_ids = get_blocked_users(user).values_list("pk", flat=True)

    following_qs = Follow.objects.filter(
        follower=user, status="accepted"
    ).values("following_id")

    return (
        Post.objects.filter(
            status=PostStatus.PUBLISHED,
            is_deleted=False,
            visibility=PostVisibility.PUBLIC,
        )
        .exclude(author=user)
        .exclude(author_id__in=following_qs)
        .exclude(author_id__in=blocked_ids)
        .select_related("author")
        .prefetch_related("media", "hashtags")
        .order_by("-created_at")
    )


def get_hashtag_feed(*, user, hashtag_name: str) -> QuerySet:
    """
    Hashtag feed: public published posts with a given hashtag.
    Excludes posts from blocked users.
    Pagination is applied by the view using CursorPagination.
    """
    blocked_ids = get_blocked_users(user).values_list("pk", flat=True)

    return (
        Post.objects.filter(
            hashtags__name__iexact=hashtag_name,
            status=PostStatus.PUBLISHED,
            is_deleted=False,
            visibility=PostVisibility.PUBLIC,
        )
        .exclude(author_id__in=blocked_ids)
        .select_related("author")
        .prefetch_related("media", "hashtags")
        .order_by("-created_at")
        .distinct()
    )
```

- [ ] **Step 4: Simplify apps/feed/services.py**

Remove the three functions that depended on Redis and Celery. Open the file and delete:
- `push_post_to_explore()` — called `explore_push()` from deleted `cache.py`
- `on_user_login()` — triggered feed warm-up task
- `on_user_unfollow()` — called `invalidate_user_feed()` from deleted `fanout.py`

Keep: `subscribe_to_hashtag()` and `unsubscribe_from_hashtag()`.

After deletion the file should be:

```python
from __future__ import annotations

import logging

from django.db import transaction

from apps.feed.models import HashtagSubscription
from apps.posts.models import Hashtag
from apps.users.selectors import get_user_by_id

logger = logging.getLogger(__name__)


@transaction.atomic
def subscribe_to_hashtag(*, user_id, hashtag_name: str) -> HashtagSubscription:
    """Subscribe a user to a hashtag so their feed includes posts with that tag."""
    user = get_user_by_id(user_id)
    hashtag, _ = Hashtag.objects.get_or_create(name=hashtag_name.lower())
    sub, _ = HashtagSubscription.objects.get_or_create(user=user, hashtag=hashtag)
    return sub


@transaction.atomic
def unsubscribe_from_hashtag(*, user_id, hashtag_name: str) -> None:
    """Unsubscribe from a hashtag."""
    user = get_user_by_id(user_id)
    HashtagSubscription.objects.filter(
        user=user, hashtag__name=hashtag_name.lower()
    ).delete()
```

- [ ] **Step 5: Rewrite apps/feed/views.py**

Replace the entire file:

```python
from __future__ import annotations

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.feed.selectors import get_explore_feed, get_hashtag_feed, get_user_feed
from apps.feed.services import subscribe_to_hashtag, unsubscribe_from_hashtag
from apps.posts.serializers import PostListSerializer
from core.pagination.cursor import CursorPagination
from rest_framework import status


class FeedView(APIView):
    """GET /api/v1/feed/"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        qs = get_user_feed(user=request.user)
        paginator = CursorPagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = PostListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class ExploreFeedView(APIView):
    """GET /api/v1/feed/explore/"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        qs = get_explore_feed(user=request.user)
        paginator = CursorPagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = PostListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class HashtagFeedView(APIView):
    """GET /api/v1/feed/hashtag/<name>/"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, name: str):
        qs = get_hashtag_feed(user=request.user, hashtag_name=name)
        paginator = CursorPagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = PostListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class HashtagSubscriptionView(APIView):
    """
    POST   /api/v1/feed/hashtags/<name>/subscribe/
    DELETE /api/v1/feed/hashtags/<name>/subscribe/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, name: str):
        subscribe_to_hashtag(user_id=request.user.pk, hashtag_name=name)
        return Response({"hashtag": name, "subscribed": True}, status=status.HTTP_201_CREATED)

    def delete(self, request: Request, name: str):
        unsubscribe_from_hashtag(user_id=request.user.pk, hashtag_name=name)
        return Response(status=status.HTTP_204_NO_CONTENT)
```

Add the missing import at the top: `from rest_framework.response import Response`

- [ ] **Step 6: Run the tests to verify they pass**

```bash
cd backend
python -m pytest apps/feed/tests/ -v
```

Expected: new selector tests pass; existing view and service tests pass.

- [ ] **Step 7: Run the full backend test suite**

```bash
cd backend
python -m pytest --tb=short -q
```

Expected: all tests pass.

- [ ] **Step 8: Commit**

```bash
git add apps/feed/ core/pagination/cursor.py
git commit -m "refactor(feed): replace Redis/Kafka pipeline with pure DB selector + CursorPagination"
```

---

## Phase 3: Report Model

### Task 8: Add Report model + moderation service cleanup + endpoint

**Files:**
- Modify: `apps/common/models.py`
- Modify: `apps/common/moderation/services.py`
- Modify: `apps/common/serializers.py`
- Modify: `apps/common/views.py`
- Modify: `apps/common/urls.py`
- Create: migration (via `makemigrations`)
- Create: `apps/common/tests/test_reports.py`

- [ ] **Step 1: Simplify apps/common/moderation/services.py**

Remove `moderate_image_async()` and the dead Prometheus import. Replace the entire file:

```python
from __future__ import annotations

import logging

from apps.common.moderation.constants import ModerationAction
from apps.common.moderation.text_filter import TextModerationFilter, TextModerationResult

logger = logging.getLogger(__name__)


def moderate_text(content: str, content_type: str = "post") -> TextModerationResult:
    """
    Run blocklist text moderation on user-submitted content.
    Raises ValidationError if content should be blocked.
    """
    result = TextModerationFilter.get_instance().check(content)

    if result.action == ModerationAction.BLOCK:
        logger.warning(
            "moderation.text.blocked",
            extra={"content_type": content_type, "rule": result.matched_rule},
        )
        from django.core.exceptions import ValidationError
        raise ValidationError(
            "Your content violates our community guidelines. "
            "Qommunity is a safe space — hate speech is not welcome here."
        )

    if result.action == ModerationAction.WARN:
        logger.info(
            "moderation.text.warned",
            extra={"content_type": content_type, "rule": result.matched_rule},
        )

    return result


def check_for_crisis_content(content: str) -> bool:
    """Return True if content contains crisis keywords."""
    return TextModerationFilter.get_instance().check_crisis_keywords(content)


def get_crisis_resources(locale: str = "DEFAULT") -> dict:
    """Return crisis resources for the given locale."""
    from apps.common.safety.constants import CRISIS_RESOURCES
    return CRISIS_RESOURCES.get(locale) or CRISIS_RESOURCES.get("DEFAULT", {})
```

- [ ] **Step 2: Write the failing tests**

Create `apps/common/tests/test_reports.py`:

```python
import pytest
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_report_post(user_factory, post_factory):
    """A user can report a post."""
    from apps.common.models import Report
    reporter = user_factory()
    post = post_factory()

    report = Report.objects.create(
        reporter=reporter, reported_post=post, reason="hate_speech"
    )
    assert report.status == "pending"
    assert report.reported_post == post
    assert report.reported_user is None
    assert report.reported_comment is None


@pytest.mark.django_db
def test_report_requires_exactly_one_target(user_factory, post_factory, comment_factory):
    """Report must have exactly one non-null target — check constraint enforced."""
    from apps.common.models import Report
    from django.db import IntegrityError

    reporter = user_factory()
    post = post_factory()
    comment = comment_factory(post=post, author=reporter)

    with pytest.raises((IntegrityError, ValidationError)):
        Report.objects.create(
            reporter=reporter,
            reported_post=post,
            reported_comment=comment,
            reason="abuse",
        )


@pytest.mark.django_db
def test_report_duplicate_prevented(user_factory, post_factory):
    """Same user cannot report the same post twice."""
    from apps.common.models import Report
    from django.db import IntegrityError

    reporter = user_factory()
    post = post_factory()
    Report.objects.create(reporter=reporter, reported_post=post, reason="harassment")

    with pytest.raises(IntegrityError):
        Report.objects.create(reporter=reporter, reported_post=post, reason="abuse")


@pytest.mark.django_db
def test_report_api_creates_report(user_factory, post_factory):
    """POST /api/v1/reports/ creates a report and returns 201."""
    reporter = user_factory()
    post = post_factory()
    client = APIClient()
    client.force_authenticate(user=reporter)

    response = client.post(
        "/api/v1/reports/",
        {"reported_post": str(post.pk), "reason": "harassment"},
        format="json",
    )
    assert response.status_code == 201
    assert response.data["status"] == "pending"


@pytest.mark.django_db
def test_report_api_requires_auth(post_factory):
    """POST /api/v1/reports/ returns 401 for unauthenticated requests."""
    post = post_factory()
    client = APIClient()
    response = client.post(
        "/api/v1/reports/",
        {"reported_post": str(post.pk), "reason": "harassment"},
        format="json",
    )
    assert response.status_code == 401
```

- [ ] **Step 3: Run the tests to verify they fail**

```bash
cd backend
python -m pytest apps/common/tests/test_reports.py -v
```

Expected: tests fail (Report model does not exist yet).

- [ ] **Step 4: Add the Report model to apps/common/models.py**

Replace the entire file (it is currently empty):

```python
from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.db.models import CheckConstraint, Q, UniqueConstraint


class Report(models.Model):
    REASON_CHOICES = [
        ("harassment",       "Harassment"),
        ("hate_speech",      "Hate Speech"),
        ("abuse",            "Abuse"),
        ("explicit_content", "Explicit Content"),
        ("other",            "Other"),
    ]
    STATUS_CHOICES = [
        ("pending",   "Pending"),
        ("reviewed",  "Reviewed"),
        ("dismissed", "Dismissed"),
    ]

    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at       = models.DateTimeField(auto_now_add=True)
    reporter         = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reports_filed"
    )
    reported_user    = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="reports_received"
    )
    reported_post    = models.ForeignKey(
        "posts.Post", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="reports"
    )
    reported_comment = models.ForeignKey(
        "comments.Comment", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="reports"
    )
    reason  = models.CharField(max_length=32, choices=REASON_CHOICES)
    details = models.TextField(blank=True)
    status  = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending")

    class Meta:
        constraints = [
            CheckConstraint(
                check=(
                    Q(reported_user__isnull=False, reported_post__isnull=True,    reported_comment__isnull=True) |
                    Q(reported_user__isnull=True,  reported_post__isnull=False,   reported_comment__isnull=True) |
                    Q(reported_user__isnull=True,  reported_post__isnull=True,    reported_comment__isnull=False)
                ),
                name="report_exactly_one_target",
            ),
            UniqueConstraint(
                fields=["reporter", "reported_user"],
                condition=Q(reported_user__isnull=False),
                name="unique_report_per_user",
            ),
            UniqueConstraint(
                fields=["reporter", "reported_post"],
                condition=Q(reported_post__isnull=False),
                name="unique_report_per_post",
            ),
            UniqueConstraint(
                fields=["reporter", "reported_comment"],
                condition=Q(reported_comment__isnull=False),
                name="unique_report_per_comment",
            ),
        ]

    def __str__(self) -> str:
        return f"Report({self.reason}) by {self.reporter_id}"
```

- [ ] **Step 5: Generate and apply the migration**

```bash
cd backend
python manage.py makemigrations common --name add_report
python manage.py migrate
```

Expected: migration file created at `apps/common/migrations/0001_add_report.py` (or next number), migration applied cleanly.

- [ ] **Step 6: Add the serializer to apps/common/serializers.py**

Replace the entire file (currently empty):

```python
from rest_framework import serializers
from apps.common.models import Report


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ["id", "reported_user", "reported_post", "reported_comment",
                  "reason", "details", "status", "created_at"]
        read_only_fields = ["id", "status", "created_at"]

    def validate(self, data):
        targets = [
            data.get("reported_user"),
            data.get("reported_post"),
            data.get("reported_comment"),
        ]
        filled = [t for t in targets if t is not None]
        if len(filled) != 1:
            raise serializers.ValidationError(
                "Exactly one of reported_user, reported_post, reported_comment must be provided."
            )
        return data
```

- [ ] **Step 7: Add the view to apps/common/views.py**

Append to the existing `apps/common/views.py` (after the health check code):

```python
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request


class ReportCreateView(APIView):
    """POST /api/v1/reports/ — create a content or user report."""
    permission_classes = [IsAuthenticated]

    def post(self, request: Request):
        from apps.common.serializers import ReportSerializer
        serializer = ReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(reporter=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
```

- [ ] **Step 8: Add the URL to apps/common/urls.py**

Replace the entire file (currently empty):

```python
from django.urls import path
from apps.common.views import ReportCreateView

app_name = "common"

urlpatterns = [
    path("", ReportCreateView.as_view(), name="report-create"),
]
```

- [ ] **Step 9: Run the tests to verify they pass**

```bash
cd backend
python -m pytest apps/common/tests/test_reports.py -v
```

Expected: all 5 tests pass.

- [ ] **Step 10: Run the full backend test suite**

```bash
cd backend
python -m pytest --tb=short -q
```

Expected: all tests pass.

- [ ] **Step 11: Commit**

```bash
git add apps/common/
git commit -m "feat(common): add Report model + POST /api/v1/reports/ endpoint"
```

---

## Phase 4: Frontend Simplification

> This phase is independent of Phases 1-3 and can be worked in parallel.

### Task 9: Remove WebSocket remnants

**Files:**
- Modify: `apps/web/src/lib/env.ts`
- Modify: `packages/types/src/notification.ts`

- [ ] **Step 1: Remove NEXT_PUBLIC_WS_URL from env.ts**

In `apps/web/src/lib/env.ts`, delete these lines from the `client` block:

```typescript
// DELETE:
NEXT_PUBLIC_WS_URL: z.string().default('ws://localhost:8000/ws'),
```

And from the `runtimeEnv` block:

```typescript
// DELETE:
NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL,
```

- [ ] **Step 2: Remove NotificationEvent from notification.ts**

In `packages/types/src/notification.ts`, delete the `NotificationEvent` interface and its comment:

```typescript
// DELETE these lines:
// WebSocket event payload — matches Django Channels broadcast
export interface NotificationEvent {
  type: 'notification.new';
  notification: Notification;
}
```

Keep the `Notification` interface and `NOTIFICATION_VERB` — these are still needed.

- [ ] **Step 3: Run type check**

```bash
cd frontend
pnpm type-check
```

Expected: no errors. If any file imported `NotificationEvent` or `env.NEXT_PUBLIC_WS_URL`, the type check will surface them — fix each import found.

- [ ] **Step 4: Commit**

```bash
git add apps/web/src/lib/env.ts packages/types/src/notification.ts
git commit -m "chore(frontend): remove WebSocket env var and NotificationEvent type"
```

---

### Task 10: Fold packages/hooks, packages/validators, packages/ui-kit into web app

**Files:**
- Move: `packages/hooks/src/` → `apps/web/src/hooks/`
- Move: `packages/validators/src/` → `apps/web/src/lib/validators/`
- Move: `packages/ui-kit/src/components/` + `primitives/` → `apps/web/src/components/ui/`
- Move: `packages/ui-kit/src/tokens/` → `apps/web/src/lib/tokens/`
- Move: `packages/ui-kit/src/lib/cn.ts` → `apps/web/src/lib/cn.ts`
- Modify: `apps/web/package.json`
- Modify: `pnpm-workspace.yaml`

- [ ] **Step 1: Copy hooks into web app**

```bash
cp -r frontend/packages/hooks/src/* frontend/apps/web/src/hooks/
```

Check if `apps/web/src/hooks/` directory exists first; create it if not:

```bash
mkdir -p frontend/apps/web/src/hooks
```

- [ ] **Step 2: Copy validators into web app**

```bash
mkdir -p frontend/apps/web/src/lib/validators
cp -r frontend/packages/validators/src/* frontend/apps/web/src/lib/validators/
```

- [ ] **Step 3: Copy ui-kit components, primitives, tokens into web app**

```bash
# Tokens
mkdir -p frontend/apps/web/src/lib/tokens
cp -r frontend/packages/ui-kit/src/tokens/* frontend/apps/web/src/lib/tokens/

# cn utility
cp frontend/packages/ui-kit/src/lib/cn.ts frontend/apps/web/src/lib/cn.ts

# Components (merge with existing ui/)
cp -r frontend/packages/ui-kit/src/components/* frontend/apps/web/src/components/ui/
cp -r frontend/packages/ui-kit/src/primitives/* frontend/apps/web/src/components/ui/
```

After copying, open `apps/web/src/components/ui/` and check for duplicates with the existing components (Button, Avatar, Input, Skeleton, etc.). For each duplicate: keep the version with more functionality, delete the other.

- [ ] **Step 4: Find all imports referencing the old package names**

```bash
cd frontend
grep -r "@qommunity/hooks" apps/web/src --include="*.ts" --include="*.tsx" -l
grep -r "@qommunity/validators" apps/web/src --include="*.ts" --include="*.tsx" -l
grep -r "@qommunity/ui-kit" apps/web/src --include="*.ts" --include="*.tsx" -l
```

For each file returned, update imports:
- `from '@qommunity/hooks'` → `from '@/hooks'`
- `from '@qommunity/validators'` → `from '@/lib/validators'`
- `from '@qommunity/ui-kit'` → `from '@/components/ui'` or `from '@/lib/tokens'`

- [ ] **Step 5: Remove the folded packages from apps/web/package.json**

In `apps/web/package.json`, find and remove the dependency entries for:
```json
"@qommunity/hooks": "workspace:*",
"@qommunity/validators": "workspace:*",
"@qommunity/ui-kit": "workspace:*"
```

- [ ] **Step 6: Remove the folded packages from pnpm-workspace.yaml**

In `pnpm-workspace.yaml`, remove:
```yaml
- packages/hooks
- packages/validators
- packages/ui-kit
```

- [ ] **Step 7: Delete the now-empty package directories**

```bash
rm -rf frontend/packages/hooks frontend/packages/validators frontend/packages/ui-kit
```

- [ ] **Step 8: Reinstall and type check**

```bash
cd frontend
pnpm install
pnpm type-check
```

Expected: no errors. Fix any broken imports surfaced by the type checker.

- [ ] **Step 9: Commit**

```bash
git add -A
git commit -m "refactor(frontend): fold hooks/validators/ui-kit packages into web app"
```

---

### Task 11: Route cleanup + notifications page

**Files:**
- Delete: `apps/web/src/app/api/users/`
- Delete: `apps/web/src/app/(main)/explore/trending/page.tsx`
- Delete: `apps/web/src/app/(main)/hashtag/[tag]/page.tsx`
- Create: `apps/web/src/app/(main)/notifications/page.tsx`

- [ ] **Step 1: Delete duplicate and out-of-scope routes**

```bash
rm -rf frontend/apps/web/src/app/api/users
rm frontend/apps/web/src/app/\(main\)/explore/trending/page.tsx
rm -rf frontend/apps/web/src/app/\(main\)/hashtag
```

- [ ] **Step 2: Verify no remaining links to deleted routes**

```bash
cd frontend
grep -r "api/users" apps/web/src --include="*.ts" --include="*.tsx"
grep -r "explore/trending" apps/web/src --include="*.ts" --include="*.tsx"
grep -r "hashtag/" apps/web/src --include="*.ts" --include="*.tsx"
```

Expected: all empty. Fix any links found before continuing.

- [ ] **Step 3: Create the notifications page**

Create `apps/web/src/app/(main)/notifications/page.tsx`:

```tsx
'use client';

import { useEffect, useState, useCallback } from 'react';
import type { Notification } from '@qommunity/types';
import { apiClient } from '@qommunity/api-client';

const POLL_INTERVAL_MS = 30_000;

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchNotifications = useCallback(async () => {
    try {
      const { data } = await apiClient.get<{ results: Notification[] }>(
        '/notifications/'
      );
      setNotifications(data.results);
      setError(null);
    } catch {
      setError('Failed to load notifications.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const markRead = useCallback(async (id: string) => {
    try {
      await apiClient.patch(`/notifications/${id}/`, { is_read: true });
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
    } catch {
      // non-critical — ignore
    }
  }, []);

  useEffect(() => {
    fetchNotifications();
    const timer = setInterval(fetchNotifications, POLL_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [fetchNotifications]);

  if (isLoading) {
    return (
      <div className="p-4">
        <p className="text-muted-foreground">Loading notifications...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4">
        <p className="text-destructive">{error}</p>
      </div>
    );
  }

  if (notifications.length === 0) {
    return (
      <div className="p-4">
        <p className="text-muted-foreground">No notifications yet.</p>
      </div>
    );
  }

  return (
    <div className="max-w-xl mx-auto p-4 space-y-2">
      <h1 className="text-xl font-semibold mb-4">Notifications</h1>
      {notifications.map((notification) => (
        <div
          key={notification.id}
          className={`p-3 rounded-lg border cursor-pointer transition-colors ${
            notification.is_read
              ? 'bg-background border-border'
              : 'bg-muted border-primary/20'
          }`}
          onClick={() => !notification.is_read && markRead(notification.id)}
        >
          <p className="text-sm">
            <span className="font-medium">{notification.actor.username}</span>{' '}
            {verbToText(notification.verb)}
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            {new Date(notification.created_at).toLocaleString()}
          </p>
        </div>
      ))}
    </div>
  );
}

function verbToText(verb: Notification['verb']): string {
  const map: Record<Notification['verb'], string> = {
    liked_post: 'liked your post',
    liked_comment: 'liked your comment',
    commented_on_post: 'commented on your post',
    replied_to_comment: 'replied to your comment',
    followed_you: 'followed you',
    follow_request: 'sent you a follow request',
    follow_request_accepted: 'accepted your follow request',
    mentioned_in_post: 'mentioned you in a post',
    mentioned_in_comment: 'mentioned you in a comment',
    post_approved: 'approved your post',
  };
  return map[verb] ?? verb;
}
```

- [ ] **Step 4: Run type check**

```bash
cd frontend
pnpm type-check
```

Expected: no errors.

- [ ] **Step 5: Verify the notifications page imports resolve**

Check that `@qommunity/api-client` exports `apiClient` (an Axios instance). Open `packages/api-client/src/instance.ts` and confirm the export name. If it differs, update the import in the notifications page.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat(frontend): add notifications page (polling), remove out-of-scope routes"
```

---

## Final Verification

- [ ] **Backend: full test suite**

```bash
cd backend
python -m pytest --tb=short -q
```

Expected: all tests pass, 0 failures.

- [ ] **Backend: Django system check**

```bash
cd backend
python manage.py check
```

Expected: `System check identified no issues (0 silenced).`

- [ ] **Frontend: type check**

```bash
cd frontend
pnpm type-check
```

Expected: no errors.

- [ ] **Final commit if any loose changes remain**

```bash
git add -A
git commit -m "chore: final cleanup after MVP simplification"
```
