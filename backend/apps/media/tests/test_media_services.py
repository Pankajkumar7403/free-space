# 📁 Location: backend/apps/media/tests/test_media_services.py
# ▶  Run:      pytest apps/media/tests/test_media_services.py -v

from unittest.mock import patch

import pytest

from apps.media.services import (
    PresignedUploadResult,
    confirm_upload,
    create_media_record,
    update_media_status,
)
from apps.posts.constants import MediaStatus, MediaType
from apps.posts.exceptions import MediaNotFoundError
from apps.posts.tests.factories import MediaFactory
from apps.users.tests.factories import UserFactory

pytestmark = [pytest.mark.unit, pytest.mark.django_db]


class TestCreateMediaRecord:
    @patch(
        "apps.media.services.generate_presigned_upload_url",
        return_value="https://fake-s3.example.com/upload",
    )
    def test_creates_media_and_returns_presigned_url(self, mock_url, db, user):
        result = create_media_record(
            owner=user, mime_type="image/jpeg", file_size=1024 * 100
        )
        assert isinstance(result, PresignedUploadResult)
        assert result.upload_url == "https://fake-s3.example.com/upload"
        assert result.media_type == MediaType.IMAGE

    @patch(
        "apps.media.services.generate_presigned_upload_url",
        return_value="https://fake-s3.example.com/upload",
    )
    def test_media_record_saved_as_pending(self, mock_url, db, user):
        from apps.posts.models import Media

        result = create_media_record(owner=user, mime_type="image/jpeg", file_size=1024)
        media = Media.objects.get(pk=result.media_id)
        assert media.status == MediaStatus.PENDING

    def test_rejects_invalid_mime_type(self, db, user):
        from apps.posts.exceptions import InvalidMediaTypeError

        with pytest.raises(InvalidMediaTypeError):
            create_media_record(owner=user, mime_type="application/exe", file_size=100)

    def test_rejects_oversized_image(self, db, user):
        from apps.posts.exceptions import FileTooLargeError

        with pytest.raises(FileTooLargeError):
            create_media_record(
                owner=user, mime_type="image/jpeg", file_size=25 * 1024 * 1024
            )


class TestConfirmUpload:
    @patch("apps.media.tasks.process_media_task.delay")
    def test_confirm_sets_uploaded_status(self, mock_task, db, user):
        media = MediaFactory(owner=user, pending=True)
        result = confirm_upload(media_id=media.pk, owner=user)
        assert result.status == MediaStatus.UPLOADED

    @patch("apps.media.tasks.process_media_task.delay")
    def test_confirm_enqueues_celery_task(self, mock_task, db, user):
        media = MediaFactory(owner=user, pending=True)
        confirm_upload(media_id=media.pk, owner=user)
        mock_task.assert_called_once_with(str(media.pk))

    def test_confirm_wrong_owner_raises(self, db, user):
        other = UserFactory()
        media = MediaFactory(owner=other, pending=True)
        with pytest.raises(MediaNotFoundError):
            confirm_upload(media_id=media.pk, owner=user)


class TestUpdateMediaStatus:
    def test_sets_ready_status(self, db, user):
        media = MediaFactory(owner=user, pending=True)
        result = update_media_status(
            media_id=str(media.pk),
            status=MediaStatus.READY,
            processed_key="processed/2025/01/abc.jpg",
            thumbnail_key="thumbnails/2025/01/abc.jpg",
            width=1080,
            height=1080,
        )
        assert result.status == MediaStatus.READY
        assert result.width == 1080

    def test_raises_for_missing_media(self, db):
        import uuid

        with pytest.raises(MediaNotFoundError):
            update_media_status(media_id=str(uuid.uuid4()), status=MediaStatus.READY)
