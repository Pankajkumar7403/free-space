# 📁 Location: backend/apps/likes/urls.py
# These are included under /api/v1/posts/ in config/urls.py

from django.urls import path

from apps.likes import views

app_name = "likes"

urlpatterns = [
    path("<uuid:post_id>/like/", views.PostLikeView.as_view(), name="post-like"),
]
