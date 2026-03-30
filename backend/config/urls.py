from django.contrib import admin
from django.urls import include, path
from django_prometheus import exports as prometheus_exports
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from apps.common.views import HealthCheckView

urlpatterns = [
    # Admin (URL kept generic - change in production via env var)
    path("admin/", admin.site.urls),
    # Health check - used by Docker/K8s probes
    path("api/v1/health/", HealthCheckView.as_view(), name="health-check"),
    # Prometheus metrics - restrict to internal network in production
    path("metrics", prometheus_exports.ExportToDjangoView, name="prometheus-metrics"),
    # API v1
    path("api/v1/users/", include("apps.users.urls", namespace="users")),
    path("api/v1/posts/", include("apps.posts.urls", namespace="posts")),
    path("api/v1/posts/", include("apps.comments.urls", namespace="comments")),
    path("api/v1/posts/", include("apps.likes.urls", namespace="likes")),
    path("api/v1/media/", include("apps.media.urls", namespace="media")),
    path("api/v1/feed/", include("apps.feed.urls", namespace="feed")),
    path(
        "api/v1/notifications/",
        include("apps.notifications.urls", namespace="notifications"),
    ),
    path("api/v1/messages/", include("apps.messaging.urls", namespace="messaging")),
    path("api/v1/gdpr/", include("apps.common.gdpr.urls", namespace="gdpr")),
    # OpenAPI schema + interactive docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
