from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.feed.selectors import get_explore_feed, get_hashtag_feed, get_user_feed
from apps.feed.services import subscribe_to_hashtag, unsubscribe_from_hashtag
from apps.posts.serializers import PostListSerializer
from core.pagination.cursor import CursorPagination


class FeedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        qs = get_user_feed(user=request.user)
        paginator = CursorPagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = PostListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class ExploreFeedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        qs = get_explore_feed(user=request.user)
        paginator = CursorPagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = PostListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class HashtagFeedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, name: str):
        qs = get_hashtag_feed(user=request.user, hashtag_name=name)
        paginator = CursorPagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = PostListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class HashtagSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, name: str):
        subscribe_to_hashtag(user_id=request.user.pk, hashtag_name=name)
        return Response({"hashtag": name, "subscribed": True}, status=status.HTTP_201_CREATED)

    def delete(self, request: Request, name: str):
        unsubscribe_from_hashtag(user_id=request.user.pk, hashtag_name=name)
        return Response(status=status.HTTP_204_NO_CONTENT)
