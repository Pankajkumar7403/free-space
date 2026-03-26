# 📁 Location: backend/apps/comments/tests/conftest.py

import pytest

from apps.comments.tests.factories import CommentFactory
from apps.posts.constants import PostVisibility
from apps.posts.tests.factories import PostFactory
from apps.users.tests.factories import UserFactory


@pytest.fixture
def post_with_comments(db, user):
    return PostFactory(author=user, visibility=PostVisibility.PUBLIC)


@pytest.fixture
def top_comment(db, post_with_comments, user):
    return CommentFactory(post=post_with_comments, author=user)


@pytest.fixture
def other_user(db):
    return UserFactory()
