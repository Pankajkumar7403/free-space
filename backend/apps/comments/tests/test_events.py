from unittest.mock import patch

import pytest

from apps.comments.events import emit_comment_created
from apps.comments.tests.factories import CommentFactory
from apps.users.tests.factories import UserFactory
from core.kafka.topics import Topics

pytestmark = [pytest.mark.unit, pytest.mark.django_db]


class TestEmitCommentCreated:
    @patch("apps.comments.events.get_producer")
    def test_top_level_comment_emits_empty_parent_fields(self, mock_get_producer):
        comment = CommentFactory()

        emit_comment_created(comment=comment)

        mock_get_producer.return_value.send.assert_called_once()
        topic, event = mock_get_producer.return_value.send.call_args.args
        payload = event.to_dict()

        assert topic == Topics.COMMENT_CREATED
        assert payload["comment_id"] == str(comment.pk)
        assert payload["post_id"] == str(comment.post_id)
        assert payload["author_id"] == str(comment.author_id)
        assert payload["post_author_id"] == str(comment.post.author_id)
        assert payload["parent_comment_id"] == ""
        assert payload["parent_comment_author_id"] == ""

    @patch("apps.comments.events.get_producer")
    def test_reply_comment_emits_parent_fields(self, mock_get_producer):
        parent_author = UserFactory()
        parent_comment = CommentFactory(author=parent_author)
        reply_comment = CommentFactory(
            post=parent_comment.post,
            parent=parent_comment,
            author=UserFactory(),
            depth=1,
        )

        emit_comment_created(comment=reply_comment)

        mock_get_producer.return_value.send.assert_called_once()
        topic, event = mock_get_producer.return_value.send.call_args.args
        payload = event.to_dict()

        assert topic == Topics.COMMENT_CREATED
        assert payload["comment_id"] == str(reply_comment.pk)
        assert payload["post_id"] == str(reply_comment.post_id)
        assert payload["author_id"] == str(reply_comment.author_id)
        assert payload["post_author_id"] == str(reply_comment.post.author_id)
        assert payload["parent_comment_id"] == str(parent_comment.pk)
        assert payload["parent_comment_author_id"] == str(parent_comment.author_id)
