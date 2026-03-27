from rest_framework.permissions import BasePermission


class IsNotificationRecipient(BasePermission):
    """Only the notification's recipient may read, mark, or delete it."""

    message = "You are not the recipient of this notification."

    def has_object_permission(self, request, view, obj) -> bool:
        return obj.recipient_id == request.user.id
