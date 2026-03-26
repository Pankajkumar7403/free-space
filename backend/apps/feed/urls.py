# 📁 Location: backend/apps/feed/urls.py
# Include in config/urls.py:
#   path("api/v1/feed/", include("apps.feed.urls", namespace="feed"))

from django.urls import path

from apps.feed import views

app_name = "feed"

urlpatterns = [
    path("", views.FeedView.as_view(), name="home"),
    path("explore/", views.ExploreFeedView.as_view(), name="explore"),
    path(
        "hashtags/<str:name>/subscribe/",
        views.HashtagSubscriptionView.as_view(),
        name="hashtag-subscribe",
    ),
]
