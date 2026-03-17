"""
core/pagination/cursor.py
~~~~~~~~~~~~~~~~~~~~~~~~~
Opaque cursor pagination — the same pattern Instagram uses.

Why cursor over page-number?
  - Page numbers break when new items are inserted (you see duplicates / miss items).
  - Cursors point to a specific row — stable even under heavy write load.
  - Scales to massive datasets without COUNT(*) queries.

Response shape
--------------
    {
        "results": [...],
        "pagination": {
            "next_cursor":     "eyJpZCI6...",   // null on last page
            "previous_cursor": "eyJpZCI6...",   // null on first page
            "count":           20               // items in this page
        }
    }

Usage in a view
---------------
    from core.pagination.cursor import CursorPagination

    class PostListView(APIView):
        def get(self, request):
            paginator = CursorPagination()
            qs = PostSelector.get_feed(user=request.user)
            page = paginator.paginate_queryset(qs, request)
            serializer = PostSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
"""
from __future__ import annotations

import base64
import json
import logging

from rest_framework.pagination import CursorPagination as DRFCursorPagination
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class CursorPagination(DRFCursorPagination):
    """
    Drop-in cursor paginator with our standardised response envelope.

    Defaults
    --------
    page_size      : 20 items per page
    max_page_size  : 100 (clients can override via ?page_size=N)
    ordering       : -created_at (newest first)
    cursor_query_param : cursor
    """

    page_size = 20
    max_page_size = 100
    page_size_query_param = "page_size"
    ordering = "-created_at"
    cursor_query_param = "cursor"

    def get_paginated_response(self, data: list) -> Response:
        return Response(
            {
                "results": data,
                "pagination": {
                    "next_cursor": self.get_next_link(),
                    "previous_cursor": self.get_previous_link(),
                    "count": len(data),
                },
            }
        )

    def get_paginated_response_schema(self, schema: dict) -> dict:
        """For drf-spectacular OpenAPI schema generation."""
        return {
            "type": "object",
            "properties": {
                "results": schema,
                "pagination": {
                    "type": "object",
                    "properties": {
                        "next_cursor": {"type": "string", "nullable": True},
                        "previous_cursor": {"type": "string", "nullable": True},
                        "count": {"type": "integer"},
                    },
                },
            },
        }


class FeedCursorPagination(CursorPagination):
    """
    Feed-specific paginator.

    The feed is ordered by score (ranking), not created_at, so we use
    a composite cursor of (score DESC, id ASC) for stable ordering.
    """

    ordering = ("-score", "id")
    page_size = 20