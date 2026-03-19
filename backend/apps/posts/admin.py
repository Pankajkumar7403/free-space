# 📁 Location: backend/apps/posts/admin.py

from django.contrib import admin
from apps.posts.models import Hashtag, Media, Post, PostHashtag, PostMedia


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display  = ("id", "author", "status", "visibility", "is_anonymous", "is_deleted", "created_at")
    list_filter   = ("status", "visibility", "is_anonymous", "is_deleted")
    search_fields = ("content", "author__username", "author__email")
    readonly_fields = ("id", "created_at", "updated_at", "search_vector")
    raw_id_fields = ("author",)

    def get_queryset(self, request):
        return Post.all_objects.all()


@admin.register(Hashtag)
class HashtagAdmin(admin.ModelAdmin):
    list_display  = ("name", "created_at")
    search_fields = ("name",)


@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display  = ("id", "owner", "media_type", "status", "file_size", "created_at")
    list_filter   = ("media_type", "status")
    search_fields = ("owner__username",)
    readonly_fields = ("id", "created_at", "updated_at")

    def get_queryset(self, request):
        return Media.all_objects.all()