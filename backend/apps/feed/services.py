from __future__ import annotations

import logging

from django.db import transaction

from apps.feed.models import HashtagSubscription
from apps.posts.models import Hashtag
from apps.users.selectors import get_user_by_id

logger = logging.getLogger(__name__)


@transaction.atomic
def subscribe_to_hashtag(*, user_id, hashtag_name: str) -> HashtagSubscription:
    """
    Subscribe a user to a hashtag so their feed includes posts with that tag.
    """
    user = get_user_by_id(user_id)
    hashtag, _ = Hashtag.objects.get_or_create(name=hashtag_name.lower())
    sub, _ = HashtagSubscription.objects.get_or_create(user=user, hashtag=hashtag)
    return sub


@transaction.atomic
def unsubscribe_from_hashtag(*, user_id, hashtag_name: str) -> None:
    """Unsubscribe from a hashtag."""
    user = get_user_by_id(user_id)
    HashtagSubscription.objects.filter(
        user=user, hashtag__name=hashtag_name.lower()
    ).delete()
