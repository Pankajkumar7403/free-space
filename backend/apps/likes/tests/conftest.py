# 📁 Location: backend/apps/likes/tests/conftest.py

import pytest
from apps.users.tests.factories import UserFactory
from apps.posts.tests.factories import PostFactory
from apps.posts.constants import PostVisibility


@pytest.fixture
def post_to_like(db, user):
    return PostFactory(author=user, visibility=PostVisibility.PUBLIC)


@pytest.fixture
def other_user(db):
    return UserFactory()