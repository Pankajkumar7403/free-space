# Qommunity MVP Simplification Design

**Date:** 2026-04-23
**Scope:** Backend (Django/DRF/PostgreSQL) + Frontend (Next.js / Turborepo)
**Goal:** Remove overengineered infrastructure and premature abstractions. Ship MVP faster without rebuilding from scratch.

---

## Context

Qommunity is an LGBTQ social media platform. The current codebase has premature scaling infrastructure (Kafka, Redis feed fanout, celebrity mode, WebSockets, Prometheus, Elasticsearch, feature flags) that adds operational complexity and cognitive overhead without delivering MVP value. This document defines exactly what to delete, simplify, and keep.

Decisions made during design:
- Celery kept only for media processing (image/video compression, transcoding, thumbnails)
- Notifications fire as direct synchronous calls from services (no Kafka, no dispatcher)
- Feed is a pure DB query (no Redis cache, no fan-out)
- Polling replaces WebSockets for notifications
- Mobile app skeleton kept untouched; all MVP work targets the web app
- `packages/types` and `packages/api-client` stay shared; `hooks`, `validators`, `ui-kit` fold into web app
- Basic text moderation (blocklist) kept; AI/ML image classification removed
- Report model added (does not exist yet in codebase)

---

## Backend

### Delete Entirely

```
core/kafka/                           # Kafka producer, consumer, topics, base_event
core/feature_flags/                   # GrowthBook client and decorators
core/monitoring/prometheus.py         # Prometheus counters and histograms
core/middleware/metrics.py            # Prometheus middleware
core/pagination/connection.py         # GraphQL-style connection pagination
core/security/app_version.py          # App version gate
core/redis/                           # Entire directory (feed ZSets, likes counters, rate limiter)
                                      # Celery broker uses CELERY_BROKER_URL in settings directly

apps/feed/fanout.py                   # Redis fan-out + celebrity mode
apps/feed/cache.py                    # Redis ZSet feed cache
apps/feed/ranking.py                  # Recency scoring (replaced by ORDER BY created_at)
apps/feed/management/                 # run_feed_consumer management command

apps/notifications/consumers.py       # Kafka-driven notification consumer
apps/notifications/dispatchers.py     # Notification dispatcher abstraction
apps/notifications/management/        # run_notification_consumer management command

apps/common/gdpr/                     # GDPR export/delete subsystem (not MVP-blocking)
apps/common/moderation/image_classifier.py   # AWS Rekognition NSFW detection (AI/ML)
apps/common/moderation/tasks.py              # Async AI image classification Celery task

apps/likes/cache.py                   # Redis like-counter cache (lost reconciliation task)

tests/load/                           # Locust load tests

# All events.py files (replaced by direct function calls):
apps/comments/events.py
apps/feed/events.py
apps/likes/events.py
apps/media/events.py
apps/notifications/events.py
apps/posts/events.py
apps/users/events.py
apps/common/events.py

# All tasks.py files except apps/media/tasks.py:
apps/comments/tasks.py
apps/feed/tasks.py
apps/likes/tasks.py
apps/notifications/tasks.py
apps/posts/tasks.py                   # Confirmed empty (1 line), safe to delete
apps/users/tasks.py
apps/common/tasks.py
```

### Remove from Settings / Dependencies

```
INSTALLED_APPS — remove:
  daphne
  channels
  django_prometheus
  django_elasticsearch_dsl
  django_celery_beat

MIDDLEWARE — remove:
  core.middleware.metrics.PrometheusMetricsMiddleware
  django_prometheus.middleware.PrometheusBeforeMiddleware
  django_prometheus.middleware.PrometheusAfterMiddleware (if present)

config/routing.py                     # WebSocket URL routing — delete file
```

### Simplify (not delete)

**`config/asgi.py`** — Trim to standard Django ASGI. Remove Channels, WebSocket routing, JWTAuthMiddlewareStack:
```python
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
application = get_asgi_application()
```

**`config/celery.py`** — Keep as-is (already minimal). Remove all beat schedules; only media tasks remain.

**`config/settings/base.py`** — Add `CELERY_BROKER_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")` directly. Remove all KAFKA_*, ELASTICSEARCH_*, CHANNEL_LAYERS, and django-prometheus settings.

**`apps/common/moderation/services.py`** — Remove `moderate_image_async()` and the Prometheus import. Keep `moderate_text()`, `check_for_crisis_content()`, and `get_crisis_resources()`.

**`apps/feed/selectors.py`** — Replace entire file with pure DB feed selector (see Feed section below).

### Keep Unchanged

```
core/database/          # BaseModel, mixins, soft_delete, transaction
core/exceptions/        # handler, error_codes, base
core/middleware/        # exception_handler, request_logging, security_headers
core/security/          # jwt, authentication, hashing, openapi
core/pagination/        # cursor.py only (connection.py deleted)
core/testing/           # base, factories, mixins
config/celery.py        # kept as-is, media tasks only
apps/users/             # auth, profiles, follow/unfollow, block/mute — all kept
apps/posts/             # models, services, selectors, views — all kept
apps/comments/          # all kept
apps/likes/             # all kept (minus cache.py and tasks.py)
apps/media/             # all kept — Celery stays here only
apps/notifications/     # kept minus consumers, dispatchers, management, events
apps/common/safety/     # CrisisResourceMiddleware kept — important for LGBTQ platform
apps/common/moderation/constants.py
apps/common/moderation/text_filter.py  # blocklist + evasion detection, no ML
```

---

## Backend: Feed Selector

Replace `apps/feed/selectors.py` with a pure DB query. No Redis, no celebrity mode, no fanout.

**Pagination:** Use `core/pagination/cursor.py` — `CursorPagination` (DRF opaque cursor, ordered by `-created_at`). The selector returns a raw `QuerySet`; the view applies `CursorPagination.paginate_queryset()`. This avoids offset-based pagination which causes duplicate or skipped posts when new content is inserted while the user scrolls.

`FeedCursorPagination` (which ordered by `-score`) is deleted along with `ranking.py` — it has no purpose in the simplified architecture.

```python
# apps/feed/selectors.py
from django.db.models import Q, QuerySet
from apps.posts.constants import PostStatus, PostVisibility
from apps.posts.models import Post
from apps.users.models import Follow
from apps.users.selectors import get_blocked_users

def get_user_feed(*, user) -> QuerySet:
    """
    Returns an ordered QuerySet for the user's home feed.
    Pagination is applied by the view using CursorPagination.
    """
    blocked_ids = get_blocked_users(user).values_list("pk", flat=True)

    following_qs = Follow.objects.filter(
        follower=user, status="accepted"
    ).values("following_id")              # subquery — stays in PostgreSQL

    own_posts = Q(author=user)            # all visibility levels including PRIVATE

    followed_posts = Q(
        author_id__in=following_qs,
        visibility__in=[
            PostVisibility.PUBLIC,
            PostVisibility.FOLLOWERS_ONLY,
            PostVisibility.CLOSE_FRIENDS, # PRIVATE from others excluded by omission
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


# apps/feed/views.py — example usage
from core.pagination.cursor import CursorPagination

class FeedView(APIView):
    def get(self, request):
        qs = get_user_feed(user=request.user)
        paginator = CursorPagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = PostSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
```

Explore and hashtag feeds retain their existing DB selectors unchanged.

---

## Backend: Notifications (Direct Service Calls)

Remove Kafka-driven dispatch. Each service calls `create_notification()` directly after the triggering action.

```python
# apps/likes/services.py — after toggle_like() creates a like
if created and like.target_author_id != requesting_user.pk:
    create_notification(
        recipient_id=like.target_author_id,
        actor_id=requesting_user.pk,
        notification_type=NotificationType.LIKE_POST,
        target_id=like.target_id,
        target_content_type_label="posts.Post",
    )

# apps/comments/services.py — after create_comment()
if comment.author_id != post.author_id:
    create_notification(
        recipient_id=post.author_id,
        actor_id=comment.author_id,
        notification_type=NotificationType.COMMENT,
        target_id=comment.pk,
        target_content_type_label="comments.Comment",
    )

# apps/users/services.py — after follow_user()
# Only notify when the follow relation is newly created.
# Guards against duplicate notifications on re-follow or duplicate requests.
follow, created = Follow.objects.get_or_create(follower=follower, following=followed_user)
if created:
    create_notification(
        recipient_id=followed_user.pk,
        actor_id=follower.pk,
        notification_type=NotificationType.FOLLOW,
        target_id=None,
        target_content_type_label=None,
    )
```

`notifications/services.py` (`create_notification`) is unchanged — it already works as a direct call.

---

## Backend: Report Model (New)

Add to `apps/common/models.py`. No generic FK — explicit nullable foreign keys with a check constraint enforcing exactly one non-null target.

```python
class Report(BaseModel):
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

    reporter         = ForeignKey(settings.AUTH_USER_MODEL, CASCADE,  related_name="reports_filed")
    reported_user    = ForeignKey(settings.AUTH_USER_MODEL, SET_NULL, null=True, blank=True, related_name="reports_received")
    reported_post    = ForeignKey("posts.Post",             SET_NULL, null=True, blank=True, related_name="reports")
    reported_comment = ForeignKey("comments.Comment",       SET_NULL, null=True, blank=True, related_name="reports")
    reason           = CharField(max_length=32, choices=REASON_CHOICES)
    details          = TextField(blank=True)
    status           = CharField(max_length=16, choices=STATUS_CHOICES, default="pending")

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
```

Add: `POST /api/reports/` — authenticated, idempotent (unique constraints prevent duplicates).

---

## Frontend

### Delete Entirely

```
packages/hooks/                                      # fold into apps/web/src/hooks/
packages/validators/                                 # fold into apps/web/src/lib/validators/
packages/ui-kit/                                     # merge into apps/web/src/components/ui/

apps/web/src/app/api/users/                          # exact duplicate of app/api/auth/ — delete
apps/web/src/app/(main)/explore/trending/page.tsx    # not in MVP scope
apps/web/src/app/(main)/hashtag/[tag]/page.tsx       # not in MVP scope

# WebSocket remnants:
env.ts: NEXT_PUBLIC_WS_URL field + runtimeEnv entry
packages/types/src/notification.ts: NotificationEvent interface
```

### Keep Unchanged

```
packages/types/          # shared with mobile skeleton
packages/api-client/     # shared with mobile skeleton
packages/config/         # tsconfig + eslint (tiny, high value)
apps/mobile/             # skeleton only — no new work

apps/web/src/stores/authStore.ts       # access token in memory — intentional security design
apps/web/src/app/api/auth/             # all 4 routes — httpOnly cookie gatekeepers
                                       # (set-cookie, session, oauth/callback, logout)
                                       # cannot be replaced by direct Django calls
```

### Move (fold packages into web app)

```
packages/hooks/src/         → apps/web/src/hooks/
packages/validators/src/    → apps/web/src/lib/validators/
packages/ui-kit/src/components/  → apps/web/src/components/ui/  (merge, deduplicate)
packages/ui-kit/src/tokens/      → apps/web/src/lib/tokens/
packages/ui-kit/src/primitives/  → apps/web/src/components/ui/  (merge with existing)
```

When merging ui-kit components with existing `apps/web/src/components/ui/`: keep one version of each component (Button, Avatar, Input, etc.), delete the duplicate.

### Add (missing MVP page)

```
apps/web/src/app/(main)/notifications/page.tsx    # polling-based, no WebSocket
```

Notifications page fetches `GET /api/notifications/` on mount and on a polling interval (e.g. 30s). No WebSocket, no EventSource.

### Resulting Web App Structure

```
apps/web/src/
  app/
    (auth)/         # login, register, forgot-password, verify-email
    (main)/         # feed, [username], explore, notifications
    api/auth/       # set-cookie, session, oauth/callback, logout
    layout.tsx
    page.tsx
    error.tsx
  components/
    features/       # auth, feed, profile, navigation
    providers/      # AppProviders, AuthProvider, ThemeProvider
    ui/             # merged primitives (Button, Input, Avatar, Skeleton, etc.)
  hooks/            # folded in from packages/hooks
  lib/
    validators/     # folded in from packages/validators
    tokens/         # folded in from packages/ui-kit/tokens
    env.ts          # remove NEXT_PUBLIC_WS_URL
    session.ts
    utils.ts
  stores/
    authStore.ts
  middleware.ts
```

---

## Future Scaling Path

When Qommunity grows beyond MVP, add back complexity in this order:

1. **Redis for caching** — Add `CELERY_RESULT_BACKEND` and Django cache layer when DB query latency becomes measurable. Feed caching is the first candidate.

2. **Async notifications** — Move `create_notification()` calls to a Celery task when notification creation starts adding measurable latency to requests (e.g. a user with many followers triggers many writes). This is a one-line change per call site — lowest effort scaling step after Redis.

3. **Celery beat tasks** — Scheduled jobs (trending hashtags, notification digests, cleanup) added to `config/celery.py` when product needs them.

4. **Feed pre-computation** — When feed queries slow down (typically >10k follows), add a `FeedItem` materialized table populated by Celery tasks on post creation. No Kafka required. This is a larger architectural change — do async notifications and beat tasks first.

5. **Kafka / event bus** — Only justified when multiple independent services need to consume the same events. Premature until you have >1 service.

6. **WebSockets** — Add back Django Channels when polling latency (30s) becomes a product complaint. The `NotificationEvent` type can be restored from git history.

7. **Celebrity mode / Redis feed fanout** — Only needed when a single post fans out to >50k followers. Monitor with DB query timing before adding.

8. **Content moderation ML** — AWS Rekognition integration is already written (`image_classifier.py` in git history). Re-enable when moderation team needs automated pre-screening.

9. **GDPR tooling** — Restore `apps/common/gdpr/` when legal requires data export/deletion workflows.

10. **Prometheus / observability** — Add back `django_prometheus` when you have a production metrics dashboard and on-call rotation.
