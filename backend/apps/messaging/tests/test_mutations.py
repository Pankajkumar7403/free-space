from unittest.mock import patch

import pytest
from rest_framework import status


@pytest.mark.django_db
class TestConversationListAPI:
    def test_list_returns_200(self, api_client, user, jwt_token_factory):
        token = jwt_token_factory(user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = api_client.get("/api/v1/messages/conversations/")
        assert response.status_code == status.HTTP_200_OK

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get("/api/v1/messages/conversations/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestDirectConversationAPI:
    def test_create_direct_returns_201(
        self, api_client, user_factory, jwt_token_factory
    ):
        user = user_factory()
        other = user_factory()
        token = jwt_token_factory(user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = api_client.post(
            "/api/v1/messages/conversations/direct/",
            data={"target_user_id": str(other.id)},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
class TestMessageListAPI:
    def test_send_message_returns_201(
        self, api_client, user_factory, jwt_token_factory
    ):
        user = user_factory()
        other = user_factory()
        token = jwt_token_factory(user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        from apps.messaging.services import create_direct_conversation

        conv, _ = create_direct_conversation(user1_id=user.id, user2_id=other.id)
        with patch("apps.messaging.views._dispatch_new_message"):
            response = api_client.post(
                f"/api/v1/messages/conversations/{conv.id}/messages/",
                data={"content": "Hello! 🌈"},
                format="json",
            )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["content"] == "Hello! 🌈"

    def test_outsider_cannot_send(self, api_client, user_factory, jwt_token_factory):
        u1 = user_factory()
        u2 = user_factory()
        outsider = user_factory()

        token = jwt_token_factory(outsider)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        from apps.messaging.services import create_direct_conversation

        conv, _ = create_direct_conversation(user1_id=u1.id, user2_id=u2.id)
        response = api_client.post(
            f"/api/v1/messages/conversations/{conv.id}/messages/",
            data={"content": "Intrude!"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
