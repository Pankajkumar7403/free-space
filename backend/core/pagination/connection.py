"""
core/pagination/connection.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Relay-style Connection / Edge wrappers.

These are used now in REST responses (for consistency with the future
GraphQL layer) and will be directly usable with Strawberry GraphQL.

Shape
-----
    {
        "edges": [
            { "node": {...}, "cursor": "abc123" },
            ...
        ],
        "pageInfo": {
            "hasNextPage":     true,
            "hasPreviousPage": false,
            "startCursor":     "abc123",
            "endCursor":       "xyz789"
        },
        "totalCount": 42     // optional — omit for huge collections
    }
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class PageInfo:
    has_next_page: bool = False
    has_previous_page: bool = False
    start_cursor: str | None = None
    end_cursor: str | None = None

    def to_dict(self) -> dict:
        return {
            "hasNextPage": self.has_next_page,
            "hasPreviousPage": self.has_previous_page,
            "startCursor": self.start_cursor,
            "endCursor": self.end_cursor,
        }


@dataclass
class Edge(Generic[T]):
    node: T
    cursor: str

    def to_dict(self) -> dict:
        return {
            "node": self.node,
            "cursor": self.cursor,
        }


@dataclass
class Connection(Generic[T]):
    edges: list[Edge[T]] = field(default_factory=list)
    page_info: PageInfo = field(default_factory=PageInfo)
    total_count: int | None = None

    def to_dict(self) -> dict:
        result: dict = {
            "edges": [e.to_dict() for e in self.edges],
            "pageInfo": self.page_info.to_dict(),
        }
        if self.total_count is not None:
            result["totalCount"] = self.total_count
        return result