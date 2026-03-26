import uuid

import pytest
from rest_framework import status
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(api_client, user_factory, jwt_token_factory):
    user = user_factory()
    token = jwt_token_factory(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client, user


@pytest.mark.django_db
class TestNotificationListAPI:

    def test_list_200(self, auth_client, notification_factory):
        client, user = auth_client
        notification_factory(recipient=user)
        notification_factory(recipient=user)
        response = client.get("/api/v1/notifications/")
        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data

    def test_unauthenticated_401(self, api_client):
        response = api_client.get("/api/v1/notifications/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unread_only_filter(self, auth_client, notification_factory):
        client, user = auth_client
        notification_factory(recipient=user, is_read=False)
        notification_factory(recipient=user, is_read=True)
        response = client.get("/api/v1/notifications/?unread_only=true")
        assert response.status_code == status.HTTP_200_OK
        for n in response.data["results"]:
            assert n["is_read"] is False


@pytest.mark.django_db
class TestUnreadCountAPI:

    def test_returns_count(self, auth_client, notification_factory):
        client, user = auth_client
        notification_factory(recipient=user, is_read=False)
        notification_factory(recipient=user, is_read=False)
        response = client.get("/api/v1/notifications/unread-count/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["unread_count"] == 2


@pytest.mark.django_db
class TestMarkReadAPI:

    def test_mark_single_read_200(self, auth_client, notification_factory):
        client, user = auth_client
        notif = notification_factory(recipient=user, is_read=False)
        response = client.patch(f"/api/v1/notifications/{notif.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_read"] is True

    def test_mark_wrong_user_403(self, auth_client, notification_factory):
        client, _ = auth_client
        other_notif = notification_factory()  # different recipient
        response = client.patch(f"/api/v1/notifications/{other_notif.id}/")
        assert response.status_code in (
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        )

    def test_mark_nonexistent_404(self, auth_client):
        client, _ = auth_client
        response = client.patch(f"/api/v1/notifications/{uuid.uuid4()}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_mark_all_read_200(self, auth_client, notification_factory):
        client, user = auth_client
        notification_factory(recipient=user, is_read=False)
        notification_factory(recipient=user, is_read=False)
        response = client.post("/api/v1/notifications/mark-all-read/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["marked_read"] == 2


@pytest.mark.django_db
class TestDeleteNotificationAPI:

    def test_delete_204(self, auth_client, notification_factory):
        client, user = auth_client
        notif = notification_factory(recipient=user)
        response = client.delete(f"/api/v1/notifications/{notif.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_wrong_user_403(self, auth_client, notification_factory):
        client, _ = auth_client
        notif = notification_factory()
        response = client.delete(f"/api/v1/notifications/{notif.id}/")
        assert response.status_code in (
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        )


@pytest.mark.django_db
class TestPreferencesAPI:

    def test_get_preferences_200(self, auth_client):
        client, _ = auth_client
        response = client.get("/api/v1/notifications/preferences/")
        assert response.status_code == status.HTTP_200_OK
        assert "likes_push" in response.data

    def test_patch_preferences(self, auth_client):
        client, _ = auth_client
        response = client.patch(
            "/api/v1/notifications/preferences/",
            data={"likes_email": True, "follows_push": False},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["likes_email"] is True
        assert response.data["follows_push"] is False


@pytest.mark.django_db
class TestDeviceTokenAPI:

    def test_register_token_201(self, auth_client):
        client, _ = auth_client
        response = client.post(
            "/api/v1/notifications/device-tokens/",
            data={"token": "valid-fcm-token", "platform": "ios"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert "id" in response.data

    def test_register_invalid_platform_400(self, auth_client):
        client, _ = auth_client
        response = client.post(
            "/api/v1/notifications/device-tokens/",
            data={"token": "tok", "platform": "nokia3310"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_deregister_token_204(
        self, auth_client, device_token_factory, user_factory
    ):
        client, user = auth_client
        device_token_factory(user=user, token="to-remove")
        response = client.delete(
            "/api/v1/notifications/device-tokens/",
            data={"token": "to-remove"},
            format="json",
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
