# 📁 Location: backend/apps/posts/urls.py
# 🔧 Include in: config/urls.py → path("api/v1/posts/", include("apps.posts.urls"))

from django.urls import path

from apps.posts import views

app_name = "posts"

urlpatterns = [
    # ── Posts ─────────────────────────────────────────────────────────────────
    path("", views.PostListCreateView.as_view(), name="list-create"),
    path("search/", views.PostSearchView.as_view(), name="search"),
    path("hashtag/<str:name>/", views.HashtagPostListView.as_view(), name="by-hashtag"),
    path(
        "hashtags/trending/",
        views.TrendingHashtagsView.as_view(),
        name="trending-hashtags",
    ),
    path("user/<uuid:user_id>/", views.UserPostListView.as_view(), name="user-posts"),
    path("<uuid:post_id>/", views.PostDetailView.as_view(), name="detail"),
    # ── Media ─────────────────────────────────────────────────────────────────
    path("media/presign/", views.MediaPresignView.as_view(), name="media-presign"),
    path(
        "media/<uuid:media_id>/confirm/",
        views.MediaConfirmView.as_view(),
        name="media-confirm",
    ),
]
