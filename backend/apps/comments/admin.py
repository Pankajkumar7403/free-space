# 📁 Location: backend/apps/comments/admin.py

from django.contrib import admin

from apps.comments.models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "author",
        "post",
        "depth",
        "is_hidden",
        "is_pinned",
        "is_flagged",
        "is_deleted",
        "created_at",
    )
    list_filter = ("depth", "is_hidden", "is_pinned", "is_flagged", "is_deleted")
    search_fields = ("content", "author__username")
    readonly_fields = ("id", "created_at", "updated_at")
    raw_id_fields = ("author", "post", "parent")

    def get_queryset(self, request):
        return Comment.all_objects.all()
