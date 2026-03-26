# 📁 Location: backend/apps/comments/urls.py
# Included in config/urls.py as:
#   path("api/v1/posts/",    include("apps.posts.urls"))
#   path("api/v1/comments/", include("apps.comments.urls"))

from django.urls import path

from apps.comments import views

app_name = "comments"

urlpatterns = [
    # Nested under posts
    path(
        "<uuid:post_id>/comments/",
        views.PostCommentListCreateView.as_view(),
        name="list-create",
    ),
    # Standalone comment operations
    path(
        "comments/<uuid:comment_id>/", views.CommentDetailView.as_view(), name="detail"
    ),
    path(
        "comments/<uuid:comment_id>/replies/",
        views.CommentRepliesView.as_view(),
        name="replies",
    ),
    path("comments/<uuid:comment_id>/pin/", views.CommentPinView.as_view(), name="pin"),
    path(
        "comments/<uuid:comment_id>/hide/", views.CommentHideView.as_view(), name="hide"
    ),
    path(
        "comments/<uuid:comment_id>/report/",
        views.CommentReportView.as_view(),
        name="report",
    ),
    path(
        "comments/<uuid:comment_id>/like/", views.CommentLikeView.as_view(), name="like"
    ),
]
