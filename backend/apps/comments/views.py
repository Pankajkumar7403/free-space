# 📁 Location: backend/apps/comments/views.py

from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.comments.selectors import (
    get_comment_by_id,
    get_comment_count,
    get_replies,
    get_top_level_comments,
)
from apps.comments.serializers import (
    CommentSerializer,
    CreateCommentSerializer,
    UpdateCommentSerializer,
)
from apps.comments.services import (
    CreateCommentInput,
    create_comment,
    delete_comment,
    hide_comment,
    pin_comment,
    report_comment,
    update_comment,
)
from core.pagination.cursor import CursorPagination


class PostCommentListCreateView(APIView):
    """
    GET  /api/v1/posts/<post_id>/comments/   → paginated top-level comments
    POST /api/v1/posts/<post_id>/comments/   → create a comment or reply
    """
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, post_id) -> Response:
        qs       = get_top_level_comments(post_id=post_id)
        total    = get_comment_count(post_id=post_id)
        paginator = CursorPagination()
        page     = paginator.paginate_queryset(qs, request)
        data     = CommentSerializer(page, many=True).data
        response = paginator.get_paginated_response(data)
        response.data["total"] = total
        return response

    def post(self, request: Request, post_id) -> Response:
        serializer = CreateCommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        comment = create_comment(CreateCommentInput(
            post_id=post_id,
            author_id=request.user.pk,
            content=d["content"],
            parent_id=d.get("parent_id"),
        ))
        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)


class CommentDetailView(APIView):
    """GET / PATCH / DELETE /api/v1/comments/<comment_id>/"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, comment_id) -> Response:
        comment = get_comment_by_id(comment_id)
        return Response(CommentSerializer(comment).data)

    def patch(self, request: Request, comment_id) -> Response:
        serializer = UpdateCommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = update_comment(
            comment_id=comment_id,
            requesting_user_id=request.user.pk,
            content=serializer.validated_data["content"],
        )
        return Response(CommentSerializer(comment).data)

    def delete(self, request: Request, comment_id) -> Response:
        delete_comment(comment_id=comment_id, requesting_user_id=request.user.pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CommentRepliesView(APIView):
    """GET /api/v1/comments/<comment_id>/replies/"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, comment_id) -> Response:
        qs        = get_replies(parent_id=comment_id)
        paginator = CursorPagination()
        page      = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(CommentSerializer(page, many=True).data)


class CommentPinView(APIView):
    """POST /api/v1/comments/<comment_id>/pin/"""
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, comment_id) -> Response:
        comment = pin_comment(
            comment_id=comment_id,
            requesting_user_id=request.user.pk,
        )
        return Response(CommentSerializer(comment).data)


class CommentHideView(APIView):
    """POST /api/v1/comments/<comment_id>/hide/"""
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, comment_id) -> Response:
        comment = hide_comment(
            comment_id=comment_id,
            requesting_user_id=request.user.pk,
        )
        return Response(CommentSerializer(comment).data)


class CommentReportView(APIView):
    """POST /api/v1/comments/<comment_id>/report/"""
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, comment_id) -> Response:
        report_comment(
            comment_id=comment_id,
            reporter_id=request.user.pk,
            reason=request.data.get("reason", "other"),
        )
        return Response({"reported": True})


class CommentLikeView(APIView):
    """POST/DELETE/GET /api/v1/comments/<comment_id>/like/"""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, comment_id) -> Response:
        from apps.likes.services import get_like_count, is_liked_by
        comment = get_comment_by_id(comment_id)
        return Response({
            "count":       get_like_count(obj=comment),
            "liked_by_me": is_liked_by(user=request.user, obj=comment),
        })

    def post(self, request: Request, comment_id) -> Response:
        from apps.likes.services import get_like_count, like_object
        comment = get_comment_by_id(comment_id)
        like_object(user=request.user, obj=comment)
        return Response(
            {"count": get_like_count(obj=comment), "liked_by_me": True},
            status=status.HTTP_201_CREATED,
        )

    def delete(self, request: Request, comment_id) -> Response:
        from apps.likes.services import get_like_count, unlike_object
        comment = get_comment_by_id(comment_id)
        unlike_object(user=request.user, obj=comment)
        return Response({"count": get_like_count(obj=comment), "liked_by_me": False})