# 📁 Location: backend/apps/feed/tests/conftest.py

import pytest

from apps.posts.tests.factories import PostFactory
from apps.users.models import Follow
from apps.users.tests.factories import UserFactory


@pytest.fixture
def author(db):
    return UserFactory(public=True)


@pytest.fixture
def follower(db):
    return UserFactory(public=True)


@pytest.fixture
def follow_relationship(db, author, follower):
    return Follow.objects.create(follower=follower, following=author, status="accepted")


@pytest.fixture
def published_post(db, author):
    from apps.posts.constants import PostVisibility

    return PostFactory(author=author, visibility=PostVisibility.PUBLIC)
