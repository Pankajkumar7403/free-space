# 📁 Location: backend/apps/posts/tests/factories.py

import factory
from apps.posts.constants import PostVisibility, PostStatus
from apps.posts.models import Hashtag, Media, Post
from apps.posts.constants import MediaStatus, MediaType
from apps.users.tests.factories import UserFactory
from core.testing.factories import BaseFactory


class HashtagFactory(BaseFactory):
    class Meta:
        model = Hashtag
        skip_postgeneration_save = True
    name = factory.Sequence(lambda n: f"tag{n}")


class MediaFactory(BaseFactory):
    class Meta:
        model = Media
        skip_postgeneration_save = True
    owner      = factory.SubFactory(UserFactory)
    media_type = MediaType.IMAGE
    status     = MediaStatus.READY
    mime_type  = "image/jpeg"
    file_size  = 1024 * 100
    original_url   = factory.Sequence(lambda n: f"https://cdn.example.com/originals/{n}.jpg")
    processed_url  = factory.Sequence(lambda n: f"https://cdn.example.com/processed/{n}.jpg")
    thumbnail_url  = factory.Sequence(lambda n: f"https://cdn.example.com/thumbnails/{n}.jpg")
    width  = 1080
    height = 1080

    class Params:
        video  = factory.Trait(media_type=MediaType.VIDEO, mime_type="video/mp4", duration=15.0)
        pending = factory.Trait(status=MediaStatus.PENDING)


class PostFactory(BaseFactory):
    class Meta:
        model = Post
        skip_postgeneration_save = True
    author     = factory.SubFactory(UserFactory)
    content    = factory.Faker("paragraph")
    visibility = PostVisibility.PUBLIC
    status     = PostStatus.PUBLISHED
    allow_comments = True
    is_anonymous   = False

    class Params:
        private        = factory.Trait(visibility=PostVisibility.PRIVATE)
        followers_only = factory.Trait(visibility=PostVisibility.FOLLOWERS_ONLY)
        anonymous      = factory.Trait(is_anonymous=True)
        no_comments    = factory.Trait(allow_comments=False)