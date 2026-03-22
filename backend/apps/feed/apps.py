# 📁 Location: backend/apps/feed/apps.py

from django.apps import AppConfig


class FeedConfig(AppConfig):
    name = "apps.feed"
    default_auto_field = "django.db.models.BigAutoField"
    verbose_name = "Feed"