from rest_framework import status
from core.exceptions.base import NotFoundError, PermissionError


class NotificationNotFoundError(NotFoundError):
    status_code = status.HTTP_404_NOT_FOUND

    def __init__(self, notification_id=None) -> None:
        super().__init__(
            code="NOTIFICATION_NOT_FOUND",
            message=(
                f"Notification{f' {notification_id}' if notification_id else ''} not found."
            ),
        )


class UnauthorizedNotificationError(PermissionError):
    status_code = status.HTTP_403_FORBIDDEN

    def __init__(self) -> None:
        super().__init__(
            code="NOTIFICATION_PERMISSION_DENIED",
            message="You do not have permission to access this notification.",
        )