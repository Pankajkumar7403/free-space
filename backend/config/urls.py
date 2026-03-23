# 📁 Location: backend/config/urls.py

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("django_prometheus.urls")),
    path("admin/", admin.site.urls),
    path("api/v1/users/", include("apps.users.urls",    namespace="users")),
    path("api/v1/posts/", include("apps.posts.urls",    namespace="posts")),
    path("api/v1/posts/", include("apps.comments.urls", namespace="comments")),
    path("api/v1/posts/", include("apps.likes.urls",    namespace="likes")),
    path("api/v1/feed/",  include("apps.feed.urls",     namespace="feed")),
]