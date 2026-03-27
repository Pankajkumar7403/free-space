# 📁 Location: backend/apps/posts/services.py

from __future__ import annotations

import re
from dataclasses import dataclass, field

from django.db import transaction

from apps.posts.constants import PostStatus, PostVisibility
from apps.posts.events import emit_post_created, emit_post_deleted
from apps.posts.exceptions import PostEditForbiddenError
from apps.posts.models import Hashtag, Post, PostHashtag
from apps.posts.selectors import get_post_by_id
from apps.posts.validators import validate_post_content
from apps.users.models import User
from apps.users.selectors import get_user_by_id

# ── Hashtag extraction ────────────────────────────────────────────────────────
_HASHTAG_RE = re.compile(r"#([a-zA-Z0-9_]{1,100})")


def extract_hashtags(content: str) -> list[str]:
    """Parse #tags from post content. Returns lowercase list, no duplicates."""
    return list({m.lower() for m in _HASHTAG_RE.findall(content)})


# ── Input dataclasses ─────────────────────────────────────────────────────────


@dataclass
class CreatePostInput:
    author_id: object
    content: str
    visibility: str = str(PostVisibility.FOLLOWERS_ONLY)
    allow_comments: bool = True
    is_anonymous: bool = False
    location_name: str = ""
    latitude: float | None = None
    longitude: float | None = None
    media_ids: list = field(default_factory=list)


@dataclass
class UpdatePostInput:
    content: str | None = None
    visibility: str | None = None
    allow_comments: bool | None = None
    location_name: str | None = None


# ── Services ──────────────────────────────────────────────────────────────────


@transaction.atomic
def create_post(data: CreatePostInput) -> Post:
    """
    Create a post, extract and upsert hashtags, attach media, emit Kafka event.

    Flow
    ----
    1. Validate content
    2. Create Post row
    3. Extract hashtags → upsert Hashtag rows → link PostHashtag
    4. Attach media items (if any)
    5. Emit post.created Kafka event (post-commit)
    """
    validate_post_content(data.content)
    author = get_user_by_id(data.author_id)

    post = Post.objects.create(
        author=author,
        content=data.content,
        visibility=data.visibility,
        allow_comments=data.allow_comments,
        is_anonymous=data.is_anonymous,
        location_name=data.location_name,
        latitude=data.latitude,
        longitude=data.longitude,
        status=PostStatus.PUBLISHED,
    )

    # ── Hashtags ──────────────────────────────────────────────────────────────
    tag_names = extract_hashtags(data.content)
    if tag_names:
        _upsert_hashtags(post, tag_names)

    # ── Media ─────────────────────────────────────────────────────────────────
    if data.media_ids:
        _attach_media(post, data.media_ids, author)

    # ── Kafka event ───────────────────────────────────────────────────────────
    # Called directly so tests can assert on it.
    # MockKafkaProducer handles dev/test — no real Kafka needed.
    emit_post_created(post)

    return post


@transaction.atomic
def update_post(*, post_id, requesting_user_id, data: UpdatePostInput) -> Post:
    """
    Update a post's mutable fields.
    Re-extracts hashtags if content changes.
    Raises PostNotFoundError, PostEditForbiddenError.
    """
    post = get_post_by_id(post_id)

    if str(post.author_id) != str(requesting_user_id):
        raise PostEditForbiddenError()

    updated_fields: list[str] = []

    if data.content is not None:
        validate_post_content(data.content)
        post.content = data.content
        updated_fields.append("content")
        # Re-sync hashtags
        tag_names = extract_hashtags(data.content)
        PostHashtag.objects.filter(post=post).delete()
        if tag_names:
            _upsert_hashtags(post, tag_names)

    if data.visibility is not None:
        post.visibility = data.visibility
        updated_fields.append("visibility")

    if data.allow_comments is not None:
        post.allow_comments = data.allow_comments
        updated_fields.append("allow_comments")

    if data.location_name is not None:
        post.location_name = data.location_name
        updated_fields.append("location_name")

    if updated_fields:
        post.save(update_fields=updated_fields)

    post.refresh_from_db()
    return post


@transaction.atomic
def delete_post(*, post_id, requesting_user_id) -> None:
    """
    Soft-delete a post. Emits post.deleted Kafka event.
    Raises PostNotFoundError, PostEditForbiddenError.
    """
    post = get_post_by_id(post_id)

    if str(post.author_id) != str(requesting_user_id):
        raise PostEditForbiddenError()

    post.soft_delete()
    emit_post_deleted(post)


# ── Internal helpers ──────────────────────────────────────────────────────────


def _upsert_hashtags(post: Post, tag_names: list[str]) -> None:
    """
    Get-or-create Hashtag rows, then bulk-create PostHashtag links.
    Uses get_or_create per tag to avoid race conditions on unique constraint.
    """
    hashtags = []
    for name in tag_names:
        hashtag, _ = Hashtag.objects.get_or_create(name=name)
        hashtags.append(hashtag)

    PostHashtag.objects.bulk_create(
        [PostHashtag(post=post, hashtag=h) for h in hashtags],
        ignore_conflicts=True,
    )


def _attach_media(post: Post, media_ids: list, author: User) -> None:
    """Attach pre-uploaded media items to a post (ownership validated)."""
    from apps.posts.models import PostMedia
    from apps.posts.selectors import get_media_by_id

    for position, media_id in enumerate(media_ids[:10]):
        media = get_media_by_id(media_id, owner=author)
        PostMedia.objects.get_or_create(
            post=post,
            media=media,
            defaults={"position": position},
        )
