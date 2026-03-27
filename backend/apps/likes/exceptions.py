# 📁 Location: backend/apps/likes/exceptions.py

from core.exceptions.base import BadRequestError, ConflictError, NotFoundError


class AlreadyLikedError(ConflictError):
    code = "ALREADY_LIKED"
    message = "You have already liked this."


class NotLikedError(BadRequestError):
    code = "NOT_LIKED"
    message = "You have not liked this."


class LikeTargetNotFoundError(NotFoundError):
    code = "LIKE_TARGET_NOT_FOUND"
    message = "The item you tried to like was not found."
