# 📁 Location: backend/apps/feed/tests/test_models.py
# ▶  Run:      pytest apps/feed/tests/test_models.py -v

import uuid

import pytest
from django.db import IntegrityError

from apps.feed.models import FeedItem, HashtagSubscription
from apps.posts.models import Hashtag

pytestmark = [pytest.mark.unit, pytest.mark.django_db]


class TestFeedItemModel:
    def test_pk_is_uuid(self, db, user):
        item = FeedItem.objects.create(user=user, post_id=uuid.uuid4(), score=0.8)
        assert isinstance(item.pk, uuid.UUID)

    def test_unique_together_user_post(self, db, user):
        pid = uuid.uuid4()
        FeedItem.objects.create(user=user, post_id=pid, score=0.5)
        with pytest.raises(IntegrityError):
            FeedItem.objects.create(user=user, post_id=pid, score=0.9)

    def test_default_source_is_follow(self, db, user):
        item = FeedItem.objects.create(user=user, post_id=uuid.uuid4())
        assert item.source == "follow"

    def test_str_representation(self, db, user):
        item = FeedItem.objects.create(user=user, post_id=uuid.uuid4())
        assert str(user.pk)[:6] in str(item) or "FeedItem" in str(item)


class TestHashtagSubscription:
    def test_subscribe_creates_record(self, db, user):
        tag = Hashtag.objects.create(name="pride")
        sub = HashtagSubscription.objects.create(user=user, hashtag=tag)
        assert sub.pk is not None

    def test_unique_together(self, db, user):
        tag = Hashtag.objects.create(name="lgbtq")
        HashtagSubscription.objects.create(user=user, hashtag=tag)
        with pytest.raises(IntegrityError):
            HashtagSubscription.objects.create(user=user, hashtag=tag)
