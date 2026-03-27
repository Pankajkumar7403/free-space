# 📁 Location: backend/apps/likes/selectors.py

from __future__ import annotations

from django.contrib.contenttypes.models import ContentType
from django.db.models import QuerySet

from apps.users.models import User


def get_likers(*, obj) -> QuerySet:
    """Return users who liked a given object, newest first."""
    ct = ContentType.objects.get_for_model(obj)
    return User.objects.filter(
        likes__content_type=ct,
        likes__object_id=obj.pk,
    ).order_by("-likes__created_at")
