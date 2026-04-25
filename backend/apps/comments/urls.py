# 📁 Location: backend/apps/comments/urls.py
# Mounted in config/urls.py as:
#   path("api/v1/comments/", include("apps.comments.urls", namespace="comments"))
#
# GET  /api/v1/comments/?post_id=<uuid>   → list top-level comments for a post
# POST /api/v1/comments/                  → create comment (post_id in request body)

from django.urls import path

from apps.comments import views

app_name = "comments"

urlpatterns = [
    path("", views.CommentListCreateView.as_view(), name="list-create"),
    path("<uuid:comment_id>/", views.CommentDetailView.as_view(), name="detail"),
    path(
        "<uuid:comment_id>/replies/",
        views.CommentRepliesView.as_view(),
        name="replies",
    ),
    path(
        "<uuid:comment_id>/like/", views.CommentLikeView.as_view(), name="like"
    ),
    path("<uuid:comment_id>/pin/", views.CommentPinView.as_view(), name="pin"),
    path(
        "<uuid:comment_id>/hide/", views.CommentHideView.as_view(), name="hide"
    ),
    path(
        "<uuid:comment_id>/report/",
        views.CommentReportView.as_view(),
        name="report",
    ),
]
