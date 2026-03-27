# 📁 Location: backend/apps/feed/views.py

from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.feed.selectors import get_explore_feed, get_user_feed
from apps.feed.services import (
    subscribe_to_hashtag,
    unsubscribe_from_hashtag,
)
from apps.posts.serializers import PostListSerializer


class FeedView(APIView):
    """
    GET /api/v1/feed/
    Returns the authenticated user's personalised ranked feed.
    Supports cursor pagination via ?cursor=<int>
    """

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        cursor = int(request.query_params.get("cursor", 0))
        page_size = min(int(request.query_params.get("page_size", 20)), 50)

        feed_page = get_user_feed(
            user=request.user,
            cursor=cursor,
            page_size=page_size,
        )

        return Response(
            {
                "results": PostListSerializer(feed_page.posts, many=True).data,
                "next_cursor": feed_page.next_cursor,
                "source": feed_page.source,
            }
        )


class ExploreFeedView(APIView):
    """
    GET /api/v1/feed/explore/
    Returns trending public posts from users the requester doesn't follow.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        cursor = int(request.query_params.get("cursor", 0))
        page_size = min(int(request.query_params.get("page_size", 20)), 50)

        feed_page = get_explore_feed(
            user=request.user,
            cursor=cursor,
            page_size=page_size,
        )

        return Response(
            {
                "results": PostListSerializer(feed_page.posts, many=True).data,
                "next_cursor": feed_page.next_cursor,
                "source": feed_page.source,
            }
        )


class HashtagSubscriptionView(APIView):
    """
    POST   /api/v1/feed/hashtags/<name>/subscribe/
    DELETE /api/v1/feed/hashtags/<name>/subscribe/
    """

    permission_classes = [IsAuthenticated]

    def post(self, request: Request, name: str) -> Response:
        subscribe_to_hashtag(user_id=request.user.pk, hashtag_name=name)
        return Response(
            {"hashtag": name, "subscribed": True}, status=status.HTTP_201_CREATED
        )

    def delete(self, request: Request, name: str) -> Response:
        unsubscribe_from_hashtag(user_id=request.user.pk, hashtag_name=name)
        return Response(status=status.HTTP_204_NO_CONTENT)
