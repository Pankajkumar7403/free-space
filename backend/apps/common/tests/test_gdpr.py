"""
apps/common/tests/test_gdpr.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Tests for GDPR data export and account deletion.
S3 and Celery are mocked - no external services needed.
"""

import uuid
from unittest.mock import patch

import pytest
from rest_framework import status
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(api_client, user_factory, jwt_token_factory):
    user = user_factory()
    user.set_password("StrongP@ss123!")
    user.save()
    token = jwt_token_factory(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client, user


# -- request_data_export service ----------------------------------------------


@pytest.mark.django_db
class TestRequestDataExport:

    @patch("apps.common.gdpr.services.generate_gdpr_export")
    def test_returns_job_id_string(self, mock_task, user_factory):
        from apps.common.gdpr.services import request_data_export

        user = user_factory()
        job_id = request_data_export(user_id=user.id)
        assert isinstance(job_id, str)
        assert len(job_id) == 36  # UUID format

    @patch("apps.common.gdpr.services.generate_gdpr_export")
    def test_queues_celery_task(self, mock_task, user_factory):
        from apps.common.gdpr.services import request_data_export

        user = user_factory()
        request_data_export(user_id=user.id)
        mock_task.delay.assert_called_once()

    @patch("apps.common.gdpr.services.generate_gdpr_export")
    def test_task_called_with_user_id(self, mock_task, user_factory):
        from apps.common.gdpr.services import request_data_export

        user = user_factory()
        request_data_export(user_id=user.id)
        call_args = mock_task.delay.call_args[0]
        assert str(user.id) in call_args

    @patch("apps.common.gdpr.services.generate_gdpr_export")
    def test_each_call_returns_unique_job_id(self, mock_task, user_factory):
        from apps.common.gdpr.services import request_data_export

        user = user_factory()
        job_1 = request_data_export(user_id=user.id)
        job_2 = request_data_export(user_id=user.id)
        assert job_1 != job_2


# -- delete_account service ---------------------------------------------------


@pytest.mark.django_db
class TestDeleteAccount:

    def test_user_is_deleted(self, user_factory):
        from apps.common.gdpr.services import delete_account
        from apps.users.models import User

        user = user_factory()
        user_id = user.id
        delete_account(user_id=user_id)
        assert not User.objects.filter(id=user_id).exists()

    def test_nonexistent_user_does_not_raise(self):
        from apps.common.gdpr.services import delete_account

        # Should not raise - gracefully handles missing user
        delete_account(user_id=uuid.uuid4())

    def test_user_notifications_deleted(self, user_factory):
        from apps.common.gdpr.services import delete_account
        from apps.notifications.models import Notification

        user = user_factory()
        Notification.objects.create(
            recipient=user,
            actor=user,
            notification_type="system",
            message="n1",
        )
        Notification.objects.create(
            recipient=user,
            actor=user,
            notification_type="system",
            message="n2",
        )
        user_id = user.id
        delete_account(user_id=user_id)
        assert Notification.objects.filter(recipient_id=user_id).count() == 0

    def test_user_posts_deleted(self, user_factory, post_factory):
        from apps.common.gdpr.services import delete_account
        from apps.posts.models import Post

        user = user_factory()
        post_factory(author=user)
        post_factory(author=user)
        user_id = user.id
        with patch("apps.common.gdpr.services.cleanup_s3_media"):
            delete_account(user_id=user_id)
        assert Post.all_objects.filter(author_id=user_id).count() == 0

    def test_user_follows_deleted(self, user_factory):
        from apps.common.gdpr.services import delete_account
        from apps.users.models import Follow

        user = user_factory()
        other = user_factory()
        Follow.objects.create(follower=user, following=other)
        Follow.objects.create(follower=other, following=user)
        user_id = user.id
        delete_account(user_id=user_id)
        assert Follow.objects.filter(follower_id=user_id).count() == 0
        assert Follow.objects.filter(following_id=user_id).count() == 0

    def test_device_tokens_deleted(self, user_factory):
        from apps.common.gdpr.services import delete_account
        from apps.notifications.models import DeviceToken

        user = user_factory()
        DeviceToken.objects.create(
            user=user,
            token="device-token-1",
            platform="android",
        )
        user_id = user.id
        delete_account(user_id=user_id)
        assert DeviceToken.objects.filter(user_id=user_id).count() == 0


# -- GDPR exporters -----------------------------------------------------------


@pytest.mark.django_db
class TestGDPRExporters:

    def test_export_profile_returns_correct_keys(self, user_factory):
        from apps.common.gdpr.exporters import _export_profile

        user = user_factory()
        result = _export_profile(user.id)
        assert "id" in result
        assert "username" in result
        assert "email" in result

    def test_export_profile_id_matches(self, user_factory):
        from apps.common.gdpr.exporters import _export_profile

        user = user_factory()
        result = _export_profile(user.id)
        assert result["id"] == str(user.id)

    def test_export_posts_returns_list(self, user_factory, post_factory):
        from apps.common.gdpr.exporters import _export_posts

        user = user_factory()
        post_factory(author=user)
        post_factory(author=user)
        result = _export_posts(user.id)
        assert isinstance(result, list)
        assert len(result) == 2

    def test_export_posts_only_user_posts(self, user_factory, post_factory):
        from apps.common.gdpr.exporters import _export_posts

        user = user_factory()
        other = user_factory()
        post_factory(author=user)
        post_factory(author=other)
        result = _export_posts(user.id)
        assert len(result) == 1

    def test_export_posts_have_required_fields(self, user_factory, post_factory):
        from apps.common.gdpr.exporters import _export_posts

        user = user_factory()
        post_factory(author=user)
        result = _export_posts(user.id)
        post = result[0]
        assert "id" in post
        assert "content" in post
        assert "created_at" in post

    def test_export_follows_returns_dict(self, user_factory):
        from apps.common.gdpr.exporters import _export_follows

        user = user_factory()
        result = _export_follows(user.id)
        assert "following" in result
        assert "followers" in result

    def test_export_notifications_returns_list(self, user_factory):
        from apps.common.gdpr.exporters import _export_notifications
        from apps.notifications.models import Notification

        user = user_factory()
        Notification.objects.create(
            recipient=user,
            actor=user,
            notification_type="system",
            message="n1",
        )
        result = _export_notifications(user.id)
        assert isinstance(result, list)
        assert len(result) == 1

    def test_export_nonexistent_user_returns_empty(self):
        from apps.common.gdpr.exporters import _export_profile

        result = _export_profile(uuid.uuid4())
        assert result == {}


# -- GDPR API views -----------------------------------------------------------


@pytest.mark.django_db
class TestGDPRDataExportAPI:

    @patch("apps.common.gdpr.services.generate_gdpr_export")
    def test_returns_202_accepted(self, mock_task, auth_client):
        client, _ = auth_client
        response = client.post(
            "/api/v1/gdpr/export/",
            data={"confirm": True},
            format="json",
        )
        assert response.status_code == status.HTTP_202_ACCEPTED

    @patch("apps.common.gdpr.services.generate_gdpr_export")
    def test_response_contains_job_id(self, mock_task, auth_client):
        client, _ = auth_client
        response = client.post(
            "/api/v1/gdpr/export/",
            data={"confirm": True},
            format="json",
        )
        assert "job_id" in response.data

    def test_requires_authentication(self, api_client):
        response = api_client.post(
            "/api/v1/gdpr/export/",
            data={"confirm": True},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_confirm_false_returns_400(self, auth_client):
        client, _ = auth_client
        response = client.post(
            "/api/v1/gdpr/export/",
            data={"confirm": False},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_confirm_returns_400(self, auth_client):
        client, _ = auth_client
        response = client.post("/api/v1/gdpr/export/", data={}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestGDPRDeleteAccountAPI:

    def test_valid_deletion_returns_200(self, auth_client):
        client, user = auth_client
        response = client.delete(
            "/api/v1/gdpr/delete-account/",
            data={
                "password": "StrongP@ss123!",
                "confirm_phrase": "DELETE MY ACCOUNT",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

    def test_wrong_password_returns_400(self, auth_client):
        client, _ = auth_client
        response = client.delete(
            "/api/v1/gdpr/delete-account/",
            data={
                "password": "WrongPassword!",
                "confirm_phrase": "DELETE MY ACCOUNT",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_wrong_confirm_phrase_returns_400(self, auth_client):
        client, _ = auth_client
        response = client.delete(
            "/api/v1/gdpr/delete-account/",
            data={
                "password": "StrongP@ss123!",
                "confirm_phrase": "delete my account",  # Wrong case
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.delete(
            "/api/v1/gdpr/delete-account/",
            data={
                "password": "anything",
                "confirm_phrase": "DELETE MY ACCOUNT",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_missing_fields_returns_400(self, auth_client):
        client, _ = auth_client
        response = client.delete(
            "/api/v1/gdpr/delete-account/",
            data={},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_successful_deletion_removes_user(self, auth_client):
        from apps.users.models import User

        client, user = auth_client
        user_id = user.id
        client.delete(
            "/api/v1/gdpr/delete-account/",
            data={
                "password": "StrongP@ss123!",
                "confirm_phrase": "DELETE MY ACCOUNT",
            },
            format="json",
        )
        assert not User.objects.filter(id=user_id).exists()
