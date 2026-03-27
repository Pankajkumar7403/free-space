"""
Root conftest.py — project-wide pytest fixtures.

Place fixtures that should be available to EVERY test here.
App-specific fixtures live in apps/<app>/tests/conftest.py.
"""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

# ── Database access ───────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def django_db_setup():
    """Use the default test database defined in config/settings/testing.py."""
    pass  # pytest-django handles this; we just document it here.


# ── Core fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture
def api_client() -> APIClient:
    """An unauthenticated DRF API client."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client: APIClient, user):
    """
    An API client force-authenticated as `user`.

    Requires a `user` fixture to be defined in the test module or a
    closer conftest.py (e.g. apps/users/tests/conftest.py).
    """
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def staff_client(api_client: APIClient, staff_user):
    """An API client authenticated as a staff user."""
    api_client.force_authenticate(user=staff_user)
    return api_client


# ── Marker auto-use ───────────────────────────────────────────────────────────


def pytest_collection_modifyitems(items):
    """
    Auto-add the 'django_db' mark to any test inside an 'integration' or
    'e2e' directory so test authors don't have to remember to add it.
    """
    for item in items:
        if "integration" in str(item.fspath) or "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.django_db)
