# 📁 Location: backend/apps/feed/admin.py

from django.contrib import admin

from apps.feed.models import FeedItem, HashtagSubscription


@admin.register(FeedItem)
class FeedItemAdmin(admin.ModelAdmin):
    list_display = ("user", "post_id", "source", "score", "created_at")
    list_filter = ("source",)
    search_fields = ("user__username",)
    readonly_fields = ("id", "created_at")


@admin.register(HashtagSubscription)
class HashtagSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "hashtag", "created_at")
    search_fields = ("user__username", "hashtag__name")
