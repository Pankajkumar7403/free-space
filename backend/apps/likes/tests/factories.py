# 📁 Location: backend/apps/likes/tests/factories.py

import factory
from django.contrib.contenttypes.models import ContentType
from apps.likes.models import Like
from apps.users.tests.factories import UserFactory
from core.testing.factories import BaseFactory


class LikeFactory(BaseFactory):
    class Meta:
        model = Like
        skip_postgeneration_save = True

    user = factory.SubFactory(UserFactory)
    # content_type and object_id set manually in tests