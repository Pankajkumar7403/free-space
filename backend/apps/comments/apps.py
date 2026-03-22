# 📁 Location: backend/apps/comments/apps.py
from django.apps import AppConfig

class CommentsConfig(AppConfig):
    name = "apps.comments"
    default_auto_field = "django.db.models.BigAutoField"
    verbose_name = "Comments"