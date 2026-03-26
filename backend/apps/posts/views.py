# 📁 Location: backend/apps/posts/views.py

from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.media.services import confirm_upload, create_media_record
from apps.posts.selectors import (
    get_post_by_id,
    get_posts_by_author,
    get_posts_by_hashtag,
    get_trending_hashtags,
    search_posts,
)
from apps.posts.serializers import (
    CreatePostSerializer,
    HashtagSerializer,
    MediaSerializer,
    PostListSerializer,
    PostSerializer,
    PresignedUrlRequestSerializer,
    UpdatePostSerializer,
)
from apps.posts.services import (
    CreatePostInput,
    UpdatePostInput,
    create_post,
    delete_post,
    update_post,
)
from apps.users.selectors import get_user_by_id
from core.pagination.cursor import CursorPagination


class PostListCreateView(APIView):
    """GET /api/v1/posts/  POST /api/v1/posts/"""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """List authenticated user's own posts."""
        qs = get_posts_by_author(request.user, requesting_user=request.user)
        paginator = CursorPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(
            PostListSerializer(page, many=True).data
        )

    def post(self, request: Request) -> Response:
        """Create a new post."""
        serializer = CreatePostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        post = create_post(
            CreatePostInput(
                author_id=request.user.pk,
                content=d["content"],
                visibility=d["visibility"],
                allow_comments=d["allow_comments"],
                is_anonymous=d["is_anonymous"],
                location_name=d.get("location_name", ""),
                latitude=d.get("latitude"),
                longitude=d.get("longitude"),
                media_ids=d.get("media_ids", []),
            )
        )
        return Response(PostSerializer(post).data, status=status.HTTP_201_CREATED)


class PostDetailView(APIView):
    """GET/PATCH/DELETE /api/v1/posts/<post_id>/"""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, post_id) -> Response:
        post = get_post_by_id(post_id, requesting_user=request.user)
        return Response(PostSerializer(post).data)

    def patch(self, request: Request, post_id) -> Response:
        serializer = UpdatePostSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        post = update_post(
            post_id=post_id,
            requesting_user_id=request.user.pk,
            data=UpdatePostInput(**serializer.validated_data),
        )
        return Response(PostSerializer(post).data)

    def delete(self, request: Request, post_id) -> Response:
        delete_post(post_id=post_id, requesting_user_id=request.user.pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserPostListView(APIView):
    """GET /api/v1/posts/user/<user_id>/"""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, user_id) -> Response:
        author = get_user_by_id(user_id)
        qs = get_posts_by_author(author, requesting_user=request.user)
        paginator = CursorPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(
            PostListSerializer(page, many=True).data
        )


class PostSearchView(APIView):
    """GET /api/v1/posts/search/?q=<query>"""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        q = request.query_params.get("q", "").strip()
        if len(q) < 2:
            return Response({"results": [], "pagination": {}})
        qs = search_posts(q, requesting_user=request.user)
        paginator = CursorPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(
            PostListSerializer(page, many=True).data
        )


class HashtagPostListView(APIView):
    """GET /api/v1/posts/hashtag/<name>/"""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, name: str) -> Response:
        qs = get_posts_by_hashtag(name)
        paginator = CursorPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(
            PostListSerializer(page, many=True).data
        )


class TrendingHashtagsView(APIView):
    """GET /api/v1/posts/hashtags/trending/"""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        hashtags = get_trending_hashtags(limit=20)
        return Response(HashtagSerializer(hashtags, many=True).data)


# ── Media views ───────────────────────────────────────────────────────────────


class MediaPresignView(APIView):
    """POST /api/v1/media/presign/ — get a presigned S3 upload URL."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = PresignedUrlRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        result = create_media_record(
            owner=request.user,
            mime_type=d["mime_type"],
            file_size=d["file_size"],
            alt_text=d.get("alt_text", ""),
        )
        return Response(
            {
                "media_id": result.media_id,
                "upload_url": result.upload_url,
                "expires_in": result.expires_in,
                "media_type": result.media_type,
            },
            status=status.HTTP_201_CREATED,
        )


class MediaConfirmView(APIView):
    """POST /api/v1/media/<media_id>/confirm/ — notify upload complete."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request, media_id) -> Response:
        media = confirm_upload(media_id=media_id, owner=request.user)
        return Response(MediaSerializer(media).data)
