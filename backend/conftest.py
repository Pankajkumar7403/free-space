# 📁 Location: backend/conftest.py   ← ROOT of your project, same level as manage.py
#
# This is the MOST IMPORTANT conftest.py — pytest finds it first.
# All fixtures here are available to every test in the entire project.

import django
import pytest
from rest_framework.test import APIClient


# ── Tell pytest-django which settings to use ─────────────────────────────────
# (Also set in pyproject.toml, but this is belt-and-suspenders)
def pytest_configure(config):
    import os
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.testing")


# ── Database fixtures ─────────────────────────────────────────────────────────

@pytest.fixture
def api_client() -> APIClient:
    """Unauthenticated DRF API client."""
    return APIClient()


# ── User fixtures (available to ALL apps) ─────────────────────────────────────
# Defined here so every app's tests can use them without importing.

@pytest.fixture
def user(db):
    """Standard active user with followers_only privacy."""
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
    """A second distinct user — useful for follow/block tests."""
    from apps.users.tests.factories import UserFactory
    return UserFactory()


@pytest.fixture
def authenticated_client(user) -> APIClient:
    """API client force-authenticated as the standard user fixture."""
    client = APIClient()
    client.force_authenticate(user=user)
    return client