# 📁 Location: backend/apps/likes/views.py

from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.likes.services import get_like_count, is_liked_by, like_object, unlike_object
from apps.posts.selectors import get_post_by_id


class PostLikeView(APIView):
    """
    POST   /api/v1/posts/<post_id>/like/   → like a post
    DELETE /api/v1/posts/<post_id>/like/   → unlike a post
    GET    /api/v1/posts/<post_id>/like/   → count + did I like it?
    """
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, post_id) -> Response:
        post  = get_post_by_id(post_id, requesting_user=request.user)
        count = get_like_count(obj=post)
        liked = is_liked_by(user=request.user, obj=post)
        return Response({"count": count, "liked_by_me": liked})

    def post(self, request: Request, post_id) -> Response:
        post = get_post_by_id(post_id, requesting_user=request.user)
        like_object(user=request.user, obj=post)
        count = get_like_count(obj=post)
        return Response({"count": count, "liked_by_me": True}, status=status.HTTP_201_CREATED)

    def delete(self, request: Request, post_id) -> Response:
        post = get_post_by_id(post_id, requesting_user=request.user)
        unlike_object(user=request.user, obj=post)
        count = get_like_count(obj=post)
        return Response({"count": count, "liked_by_me": False})