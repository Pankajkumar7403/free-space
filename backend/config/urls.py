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
    path("api/v1/users/", include("apps.users.urls", namespace="users")),
    path("api/v1/posts/", include("apps.posts.urls", namespace="posts")),
    path("api/v1/comments/", include("apps.comments.urls", namespace="comments")),
    path("api/v1/posts/", include("apps.likes.urls", namespace="likes")),
    path("api/v1/media/", include("apps.media.urls", namespace="media")),
    path("api/v1/feed/", include("apps.feed.urls", namespace="feed")),
    path("api/v1/notifications/", include("apps.notifications.urls", namespace="notifications")),
    path("api/v1/reports/", include("apps.common.urls", namespace="common")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
