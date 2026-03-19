# 📁 Location: backend/apps/posts/exceptions.py

from core.exceptions.base import NotFoundError, PermissionError, BadRequestError, ConflictError


class PostNotFoundError(NotFoundError):
    code    = "POST_NOT_FOUND"
    message = "Post not found."


class MediaNotFoundError(NotFoundError):
    code    = "MEDIA_NOT_FOUND"
    message = "Media file not found."


class PostEditForbiddenError(PermissionError):
    code    = "POST_EDIT_FORBIDDEN"
    message = "You can only edit your own posts."


class CommentsForbiddenError(BadRequestError):
    code    = "COMMENTS_DISABLED"
    message = "Comments are disabled on this post."


class MediaLimitExceededError(BadRequestError):
    code    = "MEDIA_LIMIT_EXCEEDED"
    message = "A post can have at most 10 media items."


class InvalidMediaTypeError(BadRequestError):
    code    = "INVALID_MEDIA_TYPE"
    message = "Unsupported file type. Allowed: JPEG, PNG, GIF, WebP, MP4, MOV."


class FileTooLargeError(BadRequestError):
    code    = "FILE_TOO_LARGE"
    message = "File exceeds the maximum allowed size."


class MediaNotReadyError(ConflictError):
    code    = "MEDIA_NOT_READY"
    message = "Media is still being processed. Please try again shortly."