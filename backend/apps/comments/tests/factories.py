# 📁 Location: backend/apps/comments/tests/factories.py

import factory
from apps.comments.models import Comment
from apps.posts.tests.factories import PostFactory
from apps.users.tests.factories import UserFactory
from core.testing.factories import BaseFactory


class CommentFactory(BaseFactory):
    class Meta:
        model = Comment
        skip_postgeneration_save = True

    post    = factory.SubFactory(PostFactory)
    author  = factory.SubFactory(UserFactory)
    content = factory.Faker("sentence")
    depth   = 0
    parent  = None

    class Params:
        hidden = factory.Trait(is_hidden=True)
        pinned = factory.Trait(is_pinned=True)
        flagged = factory.Trait(is_flagged=True)