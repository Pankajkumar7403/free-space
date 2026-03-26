"""
apps/users/tests/conftest.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Fixtures available to all tests inside apps/users/tests/.
"""

import pytest
from rest_framework.test import APIClient

from apps.users.tests.factories import UserFactory


@pytest.fixture
def user(db):
    """A standard active user."""
    return UserFactory()


@pytest.fixture
def staff_user(db):
    """A staff user."""
    return UserFactory(staff=True)


@pytest.fixture
def inactive_user(db):
    """A deactivated user."""
    return UserFactory(inactive=True)


@pytest.fixture
def authenticated_client(user) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=user)
    return client
