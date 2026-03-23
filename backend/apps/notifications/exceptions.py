from rest_framework import status
from core.exceptions.base import BaseAPIException
from core.exceptions.error_codes import ErrorCode


class NotificationNotFoundError(BaseAPIException):
    status_code = status.HTTP_404_NOT_FOUND

    def __init__(self, notification_id=None) -> None:
        super().__init__(
            error_code=ErrorCode.NOT_FOUND,
            message=(
                f"Notification{f' {notification_id}' if notification_id else ''} not found."
            ),
        )


class UnauthorizedNotificationError(BaseAPIException):
    status_code = status.HTTP_403_FORBIDDEN

    def __init__(self) -> None:
        super().__init__(
            error_code=ErrorCode.PERMISSION_DENIED,
            message="You do not have permission to access this notification.",
        )