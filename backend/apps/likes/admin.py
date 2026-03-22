# 📁 Location: backend/apps/likes/admin.py

from django.contrib import admin
from apps.likes.models import Like


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display  = ("user", "content_type", "object_id", "created_at")
    list_filter   = ("content_type",)
    search_fields = ("user__username",)
    readonly_fields = ("id", "created_at")