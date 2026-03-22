# 📁 Location: backend/apps/comments/permissions.py

from rest_framework.permissions import BasePermission


class CanComment(BasePermission):
    """User must be authenticated to comment."""
    message = "You must be logged in to comment."

    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated)


class CanModerate(BasePermission):
    """
    Post owner can moderate (pin, hide) comments on their posts.
    Checked at object level.
    """
    message = "Only the post owner can moderate comments."

    def has_object_permission(self, request, view, obj) -> bool:
        return str(obj.post.author_id) == str(request.user.pk)