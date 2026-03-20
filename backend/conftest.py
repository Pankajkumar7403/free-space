# 📁 Location: backend/conftest.py
# ⚠️  CRITICAL: This file must be at the ROOT of your backend/ folder,
#              the same level as manage.py. Pytest loads this first.

import pytest
from rest_framework.test import APIClient


def pytest_configure(config):
    import os
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.testing")


# ── API client ────────────────────────────────────────────────────────────────

@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


# ── User fixtures (available to ALL apps) ─────────────────────────────────────

@pytest.fixture
def user(db):
    from apps.users.tests.factories import UserFactory
    return UserFactory()


@pytest.fixture
def staff_user(db):
    from apps.users.tests.factories import UserFactory
    return UserFactory(staff=True)


@pytest.fixture
def inactive_user(db):
    from apps.users.tests.factories import UserFactory
    return UserFactory(inactive=True)


@pytest.fixture
def public_user(db):
    from apps.users.tests.factories import UserFactory
    return UserFactory(public=True)


@pytest.fixture
def private_user(db):
    from apps.users.tests.factories import UserFactory
    return UserFactory(private=True)


@pytest.fixture
def verified_user(db):
    from apps.users.tests.factories import UserFactory
    return UserFactory(verified=True)


@pytest.fixture
def other_user(db):
    from apps.users.tests.factories import UserFactory
    return UserFactory()


@pytest.fixture
def authenticated_client(user) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=user)
    return client


# ── Posts fixtures (available to ALL apps) ────────────────────────────────────

@pytest.fixture
def post(db, user):
    from apps.posts.tests.factories import PostFactory
    return PostFactory(author=user)


@pytest.fixture
def public_post(db, user):
    from apps.posts.tests.factories import PostFactory
    return PostFactory(author=user, visibility="public")


@pytest.fixture
def private_post(db, user):
    from apps.posts.tests.factories import PostFactory
    return PostFactory(author=user, private=True)


@pytest.fixture
def ready_media(db, user):
    from apps.posts.tests.factories import MediaFactory
    return MediaFactory(owner=user)


@pytest.fixture
def pending_media(db, user):
    from apps.posts.tests.factories import MediaFactory
    return MediaFactory(owner=user, pending=True)


# ── Feed fixtures (available to ALL apps) ─────────────────────────────────────

@pytest.fixture
def follow_relationship(db, user, other_user):
    from apps.users.models import Follow
    return Follow.objects.create(follower=user, following=other_user, status="accepted")