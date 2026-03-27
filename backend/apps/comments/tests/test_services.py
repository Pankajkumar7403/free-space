# 📁 Location: backend/apps/comments/tests/test_services.py
# ▶  Run:      pytest apps/comments/tests/test_services.py -v

from unittest.mock import patch

import pytest

from apps.comments.exceptions import (
    CommentDepthExceededError,
    CommentEditForbiddenError,
    CommentsDisabledError,
)
from apps.comments.models import Comment
from apps.comments.services import (
    CreateCommentInput,
    create_comment,
    delete_comment,
    hide_comment,
    pin_comment,
    update_comment,
)
from apps.comments.tests.factories import CommentFactory
from apps.posts.constants import PostVisibility
from apps.posts.tests.factories import PostFactory
from apps.users.tests.factories import UserFactory

pytestmark = [pytest.mark.unit, pytest.mark.django_db]


class TestCreateComment:
    @patch("apps.comments.services.emit_comment_created")
    def test_creates_top_level_comment(self, mock_emit, db, user):
        post = PostFactory(author=UserFactory(), visibility=PostVisibility.PUBLIC)
        comment = create_comment(
            CreateCommentInput(
                post_id=post.pk, author_id=user.pk, content="Great post!"
            )
        )
        assert comment.pk is not None
        assert comment.depth == 0
        assert comment.parent is None

    @patch("apps.comments.services.emit_comment_created")
    def test_creates_reply_with_depth_1(self, mock_emit, db, user):
        post = PostFactory(author=UserFactory(), visibility=PostVisibility.PUBLIC)
        parent = CommentFactory(post=post, author=user)
        reply = create_comment(
            CreateCommentInput(
                post_id=post.pk,
                author_id=user.pk,
                content="I agree!",
                parent_id=parent.pk,
            )
        )
        assert reply.depth == 1
        assert str(reply.parent_id) == str(parent.pk)

    @patch("apps.comments.services.emit_comment_created")
    def test_creates_depth_2_reply(self, mock_emit, db, user):
        post = PostFactory(author=UserFactory(), visibility=PostVisibility.PUBLIC)
        level0 = CommentFactory(post=post, author=user, depth=0)
        level1 = CommentFactory(post=post, author=user, parent=level0, depth=1)
        level2 = create_comment(
            CreateCommentInput(
                post_id=post.pk,
                author_id=user.pk,
                content="Nested reply",
                parent_id=level1.pk,
            )
        )
        assert level2.depth == 2

    @patch("apps.comments.services.emit_comment_created")
    def test_raises_on_depth_3(self, mock_emit, db, user):
        post = PostFactory(author=UserFactory(), visibility=PostVisibility.PUBLIC)
        level0 = CommentFactory(post=post, author=user, depth=0)
        level1 = CommentFactory(post=post, author=user, parent=level0, depth=1)
        level2 = CommentFactory(post=post, author=user, parent=level1, depth=2)
        with pytest.raises(CommentDepthExceededError):
            create_comment(
                CreateCommentInput(
                    post_id=post.pk,
                    author_id=user.pk,
                    content="Too deep!",
                    parent_id=level2.pk,
                )
            )

    def test_raises_when_comments_disabled(self, db, user):
        post = PostFactory(
            author=UserFactory(),
            visibility=PostVisibility.PUBLIC,
            no_comments=True,
        )
        with pytest.raises(CommentsDisabledError):
            create_comment(
                CreateCommentInput(
                    post_id=post.pk, author_id=user.pk, content="Can I comment?"
                )
            )

    @patch("apps.comments.services.emit_comment_created")
    def test_auto_flags_hate_speech(self, mock_emit, db, user):
        post = PostFactory(author=UserFactory(), visibility=PostVisibility.PUBLIC)
        comment = create_comment(
            CreateCommentInput(
                post_id=post.pk,
                author_id=user.pk,
                content="You are a faggot",  # contains flagged keyword
            )
        )
        assert comment.is_flagged is True

    @patch("apps.comments.services.emit_comment_created")
    def test_emits_kafka_event(self, mock_emit, db, user):
        post = PostFactory(author=UserFactory(), visibility=PostVisibility.PUBLIC)
        create_comment(
            CreateCommentInput(post_id=post.pk, author_id=user.pk, content="Hello")
        )
        mock_emit.assert_called_once()


class TestUpdateComment:
    @patch("apps.comments.services.emit_comment_created")
    def test_updates_content(self, mock_emit, db, user):
        post = PostFactory(author=UserFactory(), visibility=PostVisibility.PUBLIC)
        comment = create_comment(
            CreateCommentInput(post_id=post.pk, author_id=user.pk, content="original")
        )
        updated = update_comment(
            comment_id=comment.pk,
            requesting_user_id=user.pk,
            content="updated",
        )
        assert updated.content == "updated"

    @patch("apps.comments.services.emit_comment_created")
    def test_raises_if_not_author(self, mock_emit, db, user):
        other = UserFactory()
        post = PostFactory(author=UserFactory(), visibility=PostVisibility.PUBLIC)
        comment = create_comment(
            CreateCommentInput(post_id=post.pk, author_id=user.pk, content="mine")
        )
        with pytest.raises(CommentEditForbiddenError):
            update_comment(
                comment_id=comment.pk,
                requesting_user_id=other.pk,
                content="hacked",
            )


class TestDeleteComment:
    @patch("apps.comments.services.emit_comment_created")
    def test_author_can_delete(self, mock_emit, db, user):
        post = PostFactory(author=UserFactory(), visibility=PostVisibility.PUBLIC)
        comment = create_comment(
            CreateCommentInput(post_id=post.pk, author_id=user.pk, content="delete me")
        )
        delete_comment(comment_id=comment.pk, requesting_user_id=user.pk)
        assert not Comment.objects.filter(pk=comment.pk).exists()

    @patch("apps.comments.services.emit_comment_created")
    def test_post_owner_can_delete(self, mock_emit, db, user):
        """Post owner can delete any comment on their post."""
        post_owner = UserFactory()
        commenter = UserFactory()
        post = PostFactory(author=post_owner, visibility=PostVisibility.PUBLIC)
        comment = create_comment(
            CreateCommentInput(
                post_id=post.pk, author_id=commenter.pk, content="rude comment"
            )
        )
        delete_comment(comment_id=comment.pk, requesting_user_id=post_owner.pk)
        assert not Comment.objects.filter(pk=comment.pk).exists()

    @patch("apps.comments.services.emit_comment_created")
    def test_third_party_cannot_delete(self, mock_emit, db, user):
        stranger = UserFactory()
        post = PostFactory(author=UserFactory(), visibility=PostVisibility.PUBLIC)
        comment = create_comment(
            CreateCommentInput(post_id=post.pk, author_id=user.pk, content="mine")
        )
        with pytest.raises(CommentEditForbiddenError):
            delete_comment(comment_id=comment.pk, requesting_user_id=stranger.pk)


class TestPinComment:
    @patch("apps.comments.services.emit_comment_created")
    def test_post_owner_can_pin(self, mock_emit, db):
        owner = UserFactory()
        commenter = UserFactory()
        post = PostFactory(author=owner, visibility=PostVisibility.PUBLIC)
        comment = create_comment(
            CreateCommentInput(
                post_id=post.pk, author_id=commenter.pk, content="great post!"
            )
        )
        pinned = pin_comment(comment_id=comment.pk, requesting_user_id=owner.pk)
        assert pinned.is_pinned is True

    @patch("apps.comments.services.emit_comment_created")
    def test_pinning_unpins_previous(self, mock_emit, db):
        """Only one comment can be pinned at a time."""
        owner = UserFactory()
        post = PostFactory(author=owner, visibility=PostVisibility.PUBLIC)
        c1 = create_comment(
            CreateCommentInput(post_id=post.pk, author_id=owner.pk, content="first")
        )
        c2 = create_comment(
            CreateCommentInput(post_id=post.pk, author_id=owner.pk, content="second")
        )
        pin_comment(comment_id=c1.pk, requesting_user_id=owner.pk)
        pin_comment(comment_id=c2.pk, requesting_user_id=owner.pk)
        c1.refresh_from_db()
        assert c1.is_pinned is False

    @patch("apps.comments.services.emit_comment_created")
    def test_non_owner_cannot_pin(self, mock_emit, db, user):
        post = PostFactory(author=UserFactory(), visibility=PostVisibility.PUBLIC)
        comment = create_comment(
            CreateCommentInput(post_id=post.pk, author_id=user.pk, content="hi")
        )
        with pytest.raises(CommentEditForbiddenError):
            pin_comment(comment_id=comment.pk, requesting_user_id=user.pk)


class TestHideComment:
    @patch("apps.comments.services.emit_comment_created")
    def test_author_can_hide_own_comment(self, mock_emit, db, user):
        post = PostFactory(author=UserFactory(), visibility=PostVisibility.PUBLIC)
        comment = create_comment(
            CreateCommentInput(post_id=post.pk, author_id=user.pk, content="hide me")
        )
        hidden = hide_comment(comment_id=comment.pk, requesting_user_id=user.pk)
        assert hidden.is_hidden is True

    @patch("apps.comments.services.emit_comment_created")
    def test_post_owner_can_hide_any_comment(self, mock_emit, db):
        owner = UserFactory()
        commenter = UserFactory()
        post = PostFactory(author=owner, visibility=PostVisibility.PUBLIC)
        comment = create_comment(
            CreateCommentInput(
                post_id=post.pk, author_id=commenter.pk, content="offensive"
            )
        )
        hidden = hide_comment(comment_id=comment.pk, requesting_user_id=owner.pk)
        assert hidden.is_hidden is True
