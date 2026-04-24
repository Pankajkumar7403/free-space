# 📁 Location: backend/apps/likes/tests/test_services.py

from unittest.mock import patch

import pytest

from apps.likes.exceptions import AlreadyLikedError, NotLikedError
from apps.likes.services import get_like_count, is_liked_by, like_object, unlike_object


@pytest.mark.django_db
def test_like_post_creates_notification(user_factory, post_factory):
    """Liking a post fires a notification to the post author."""
    author = user_factory()
    liker = user_factory()
    post = post_factory(author=author)

    with patch("apps.notifications.services.create_notification") as mock_notify:
        like_object(user=liker, obj=post)
        mock_notify.assert_called_once()
        call_kwargs = mock_notify.call_args.kwargs
        assert str(call_kwargs["recipient_id"]) == str(author.pk)
        assert str(call_kwargs["actor_id"]) == str(liker.pk)


@pytest.mark.django_db
def test_like_post_no_self_notification(user_factory, post_factory):
    """Liking your own post does not create a notification."""
    user = user_factory()
    post = post_factory(author=user)

    with patch("apps.notifications.services.create_notification") as mock_notify:
        like_object(user=user, obj=post)
        mock_notify.assert_not_called()


@pytest.mark.django_db
def test_like_post_duplicate_raises(user_factory, post_factory):
    """Liking the same post twice raises AlreadyLikedError."""
    user = user_factory()
    post = post_factory()
    like_object(user=user, obj=post)
    with pytest.raises(AlreadyLikedError):
        like_object(user=user, obj=post)


@pytest.mark.django_db
def test_get_like_count_from_db(user_factory, post_factory):
    """get_like_count returns DB count."""
    liker1 = user_factory()
    liker2 = user_factory()
    post = post_factory()
    like_object(user=liker1, obj=post)
    like_object(user=liker2, obj=post)
    assert get_like_count(obj=post) == 2


@pytest.mark.django_db
def test_is_liked_by_db(user_factory, post_factory):
    """is_liked_by uses DB."""
    user = user_factory()
    post = post_factory()
    assert is_liked_by(user=user, obj=post) is False
    like_object(user=user, obj=post)
    assert is_liked_by(user=user, obj=post) is True
