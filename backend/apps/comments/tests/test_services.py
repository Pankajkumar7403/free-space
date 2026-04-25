# 📁 Location: backend/apps/comments/tests/test_services.py

from unittest.mock import patch

import pytest

from apps.comments.services import CreateCommentInput, create_comment


@pytest.mark.django_db
def test_comment_notifies_post_author(user_factory, post_factory):
    """Commenting on a post notifies the post author."""
    author = user_factory()
    commenter = user_factory()
    post = post_factory(author=author, allow_comments=True)

    with patch("apps.notifications.services.create_notification") as mock_notify:
        create_comment(CreateCommentInput(
            post_id=post.pk, author_id=commenter.pk, content="Nice post!"
        ))
        mock_notify.assert_called_once()
        assert mock_notify.call_args.kwargs["recipient_id"] == author.pk
        assert mock_notify.call_args.kwargs["actor_id"] == commenter.pk


@pytest.mark.django_db
def test_comment_no_self_notification(user_factory, post_factory):
    """Commenting on your own post does not notify yourself."""
    user = user_factory()
    post = post_factory(author=user, allow_comments=True)

    with patch("apps.notifications.services.create_notification") as mock_notify:
        create_comment(CreateCommentInput(
            post_id=post.pk, author_id=user.pk, content="My own post!"
        ))
        mock_notify.assert_not_called()


@pytest.mark.django_db
def test_reply_notifies_parent_comment_author(user_factory, post_factory, comment_factory):
    """Replying to a comment notifies both post author and parent comment author."""
    post_author = user_factory()
    commenter = user_factory()
    replier = user_factory()
    post = post_factory(author=post_author, allow_comments=True)
    parent = comment_factory(post=post, author=commenter)

    with patch("apps.notifications.services.create_notification") as mock_notify:
        create_comment(CreateCommentInput(
            post_id=post.pk, author_id=replier.pk,
            content="Nice comment!", parent_id=parent.pk,
        ))
        recipient_ids = {c.kwargs["recipient_id"] for c in mock_notify.call_args_list}
        assert post_author.pk in recipient_ids
        assert commenter.pk in recipient_ids
