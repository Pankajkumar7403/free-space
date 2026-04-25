import pytest
from django.db import IntegrityError
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_report_post(user_factory, post_factory):
    from apps.common.models import Report
    reporter = user_factory()
    post = post_factory()
    report = Report.objects.create(reporter=reporter, reported_post=post, reason="hate_speech")
    assert report.status == "pending"
    assert report.reported_post == post
    assert report.reported_user is None
    assert report.reported_comment is None


@pytest.mark.django_db
def test_report_duplicate_prevented(user_factory, post_factory):
    from apps.common.models import Report
    reporter = user_factory()
    post = post_factory()
    Report.objects.create(reporter=reporter, reported_post=post, reason="harassment")
    with pytest.raises(IntegrityError):
        Report.objects.create(reporter=reporter, reported_post=post, reason="abuse")


@pytest.mark.django_db
def test_report_api_creates_report(user_factory, post_factory):
    reporter = user_factory()
    post = post_factory()
    client = APIClient()
    client.force_authenticate(user=reporter)
    response = client.post(
        "/api/v1/reports/",
        {"reported_post": str(post.pk), "reason": "harassment"},
        format="json",
    )
    assert response.status_code == 201
    assert response.data["status"] == "pending"


@pytest.mark.django_db
def test_report_api_requires_auth(post_factory):
    post = post_factory()
    client = APIClient()
    response = client.post(
        "/api/v1/reports/",
        {"reported_post": str(post.pk), "reason": "harassment"},
        format="json",
    )
    assert response.status_code == 401
