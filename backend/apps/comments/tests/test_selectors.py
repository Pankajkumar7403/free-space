# 📁 Location: backend/apps/comments/tests/test_selectors.py
# ▶  Run:      pytest apps/comments/tests/test_selectors.py -v

import pytest

from apps.comments.exceptions import CommentNotFoundError
from apps.comments.selectors import (
    get_comment_by_id,
    get_comment_count,
    get_replies,
    get_top_level_comments,
)
from apps.comments.tests.factories import CommentFactory
from apps.posts.constants import PostVisibility
from apps.posts.tests.factories import PostFactory

pytestmark = [pytest.mark.unit, pytest.mark.django_db]


class TestGetCommentById:
    def test_returns_existing_comment(self, db, user):
        post = PostFactory(author=user, visibility=PostVisibility.PUBLIC)
        comment = CommentFactory(post=post, author=user)
        result = get_comment_by_id(comment.pk)
        assert result.pk == comment.pk

    def test_raises_for_deleted_comment(self, db, user):
        post = PostFactory(author=user, visibility=PostVisibility.PUBLIC)
        comment = CommentFactory(post=post, author=user)
        comment.soft_delete()
        with pytest.raises(CommentNotFoundError):
            get_comment_by_id(comment.pk)

    def test_raises_for_missing_id(self, db):
        import uuid

        with pytest.raises(CommentNotFoundError):
            get_comment_by_id(uuid.uuid4())


class TestGetTopLevelComments:
    def test_returns_only_top_level(self, db, user):
        post = PostFactory(author=user, visibility=PostVisibility.PUBLIC)
        top = CommentFactory(post=post, author=user, depth=0)
        reply = CommentFactory(post=post, author=user, parent=top, depth=1)
        results = list(get_top_level_comments(post_id=post.pk))
        assert top in results
        assert reply not in results

    def test_pinned_comment_returned_first(self, db, user):
        post = PostFactory(author=user, visibility=PostVisibility.PUBLIC)
        CommentFactory(post=post, author=user)
        pinned = CommentFactory(post=post, author=user, pinned=True)
        results = list(get_top_level_comments(post_id=post.pk))
        assert results[0].pk == pinned.pk

    def test_excludes_soft_deleted(self, db, user):
        post = PostFactory(author=user, visibility=PostVisibility.PUBLIC)
        comment = CommentFactory(post=post, author=user)
        comment.soft_delete()
        results = list(get_top_level_comments(post_id=post.pk))
        assert comment not in results


class TestGetReplies:
    def test_returns_direct_replies_only(self, db, user):
        post = PostFactory(author=user, visibility=PostVisibility.PUBLIC)
        parent = CommentFactory(post=post, author=user, depth=0)
        reply1 = CommentFactory(post=post, author=user, parent=parent, depth=1)
        reply2 = CommentFactory(post=post, author=user, parent=parent, depth=1)
        other = CommentFactory(post=post, author=user, depth=0)
        results = list(get_replies(parent_id=parent.pk))
        assert reply1 in results
        assert reply2 in results
        assert other not in results

    def test_ordered_oldest_first(self, db, user):
        post = PostFactory(author=user, visibility=PostVisibility.PUBLIC)
        parent = CommentFactory(post=post, author=user)
        r1 = CommentFactory(post=post, author=user, parent=parent, depth=1)
        CommentFactory(post=post, author=user, parent=parent, depth=1)
        results = list(get_replies(parent_id=parent.pk))
        assert results[0].pk == r1.pk


class TestGetCommentCount:
    def test_counts_visible_comments(self, db, user):
        post = PostFactory(author=user, visibility=PostVisibility.PUBLIC)
        CommentFactory(post=post, author=user)
        CommentFactory(post=post, author=user)
        assert get_comment_count(post_id=post.pk) == 2

    def test_excludes_hidden_comments(self, db, user):
        post = PostFactory(author=user, visibility=PostVisibility.PUBLIC)
        CommentFactory(post=post, author=user)
        CommentFactory(post=post, author=user, hidden=True)
        assert get_comment_count(post_id=post.pk) == 1

    def test_excludes_deleted_comments(self, db, user):
        post = PostFactory(author=user, visibility=PostVisibility.PUBLIC)
        comment = CommentFactory(post=post, author=user)
        comment.soft_delete()
        assert get_comment_count(post_id=post.pk) == 0
