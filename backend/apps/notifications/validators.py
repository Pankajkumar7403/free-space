from django.core.exceptions import ValidationError

from apps.notifications.constants import DevicePlatform


def validate_device_token(token: str) -> None:
    if not token or not token.strip():
        raise ValidationError("Device token cannot be empty.")
    if len(token) > 512:
        raise ValidationError("Device token must not exceed 512 characters.")


def validate_platform(platform: str) -> None:
    valid = [p.value for p in DevicePlatform]
    if platform not in valid:
        raise ValidationError(
            f"Platform '{platform}' is not supported. Choose from: {valid}."
        )