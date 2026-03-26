# 📁 Location: backend/apps/posts/tests/conftest.py

import pytest

from apps.posts.tests.factories import HashtagFactory, MediaFactory, PostFactory


@pytest.fixture
def post(db, user):
    return PostFactory(author=user)


@pytest.fixture
def public_post(db, user):
    return PostFactory(author=user, visibility="public")


@pytest.fixture
def private_post(db, user):
    return PostFactory(author=user, private=True)


@pytest.fixture
def hashtag(db):
    return HashtagFactory()


@pytest.fixture
def ready_media(db, user):
    return MediaFactory(owner=user)


@pytest.fixture
def pending_media(db, user):
    return MediaFactory(owner=user, pending=True)
