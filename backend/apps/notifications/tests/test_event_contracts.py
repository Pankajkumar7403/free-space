import uuid
from unittest.mock import patch

from apps.notifications.events import handle_kafka_event


class TestHandleKafkaEventContracts:
    @patch("apps.notifications.events.create_notification")
    def test_like_created_contract_maps_canonical_payload(self, mock_create_notification):
        actor_id = uuid.uuid4()
        recipient_id = uuid.uuid4()
        object_id = uuid.uuid4()

        payload = {
            "like_id": str(uuid.uuid4()),
            "user_id": str(actor_id),
            "object_id": str(object_id),
            "object_type": "post",
            "author_id": str(recipient_id),
        }

        handle_kafka_event(topic="like.created", value=payload)

        mock_create_notification.assert_called_once_with(
            recipient_id=recipient_id,
            actor_id=actor_id,
            notification_type="like_post",
            target_id=object_id,
            target_content_type_label="posts.Post",
        )

    @patch("apps.notifications.events.create_notification")
    def test_like_created_comment_contract_maps_to_like_comment(
        self, mock_create_notification
    ):
        actor_id = uuid.uuid4()
        recipient_id = uuid.uuid4()
        object_id = uuid.uuid4()

        payload = {
            "like_id": str(uuid.uuid4()),
            "user_id": str(actor_id),
            "object_id": str(object_id),
            "object_type": "comment",
            "author_id": str(recipient_id),
        }

        handle_kafka_event(topic="like.created", value=payload)

        mock_create_notification.assert_called_once_with(
            recipient_id=recipient_id,
            actor_id=actor_id,
            notification_type="like_comment",
            target_id=object_id,
            target_content_type_label="comments.Comment",
        )

    @patch("apps.notifications.events.create_notification")
    def test_like_created_contract_supports_legacy_payload(self, mock_create_notification):
        actor_id = uuid.uuid4()
        recipient_id = uuid.uuid4()
        object_id = uuid.uuid4()

        payload = {
            "liker_id": str(actor_id),
            "post_author_id": str(recipient_id),
            "post_id": str(object_id),
        }

        handle_kafka_event(topic="like.created", value=payload)

        mock_create_notification.assert_called_once_with(
            recipient_id=recipient_id,
            actor_id=actor_id,
            notification_type="like_post",
            target_id=object_id,
            target_content_type_label="posts.Post",
        )

    @patch("apps.notifications.events.create_notification")
    def test_comment_created_contract_maps_canonical_payload(
        self, mock_create_notification
    ):
        actor_id = uuid.uuid4()
        post_author_id = uuid.uuid4()
        comment_id = uuid.uuid4()

        payload = {
            "comment_id": str(comment_id),
            "post_id": str(uuid.uuid4()),
            "author_id": str(actor_id),
            "post_author_id": str(post_author_id),
        }

        handle_kafka_event(topic="comment.created", value=payload)

        mock_create_notification.assert_called_once_with(
            recipient_id=post_author_id,
            actor_id=actor_id,
            notification_type="comment",
            target_id=comment_id,
            target_content_type_label="comments.Comment",
        )

    @patch("apps.notifications.events.create_notification")
    def test_user_followed_contract_maps_canonical_payload(self, mock_create_notification):
        follower_id = uuid.uuid4()
        following_id = uuid.uuid4()

        payload = {
            "follower_id": str(follower_id),
            "following_id": str(following_id),
        }

        handle_kafka_event(topic="user.followed", value=payload)

        mock_create_notification.assert_called_once_with(
            recipient_id=following_id,
            actor_id=follower_id,
            notification_type="follow",
            target_id=None,
            target_content_type_label=None,
        )
