# 📁 Location: backend/apps/comments/exceptions.py

from core.exceptions.base import BadRequestError, NotFoundError, PermissionError


class CommentNotFoundError(NotFoundError):
    code = "COMMENT_NOT_FOUND"
    message = "Comment not found."


class CommentEditForbiddenError(PermissionError):
    code = "COMMENT_EDIT_FORBIDDEN"
    message = "You can only edit your own comments."


class CommentDepthExceededError(BadRequestError):
    code = "COMMENT_DEPTH_EXCEEDED"
    message = "Replies can only be nested 2 levels deep."


class CommentsDisabledError(BadRequestError):
    code = "COMMENTS_DISABLED"
    message = "Comments are disabled on this post."


class CommentHiddenError(BadRequestError):
    code = "COMMENT_HIDDEN"
    message = "This comment has been hidden."
