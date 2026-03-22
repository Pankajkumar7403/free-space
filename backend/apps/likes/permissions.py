# 📁 Location: backend/apps/likes/permissions.py

from rest_framework.permissions import BasePermission, IsAuthenticated


class CanLike(BasePermission):
    """
    Allow liking only if:
    - User is authenticated
    - User is verified (email confirmed)
    """
    message = "You must verify your email before liking posts."

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
        )