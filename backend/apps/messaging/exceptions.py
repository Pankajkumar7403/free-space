from core.exceptions.base import (
    ConflictError,
    NotFoundError,
    PermissionError,
    ValidationError,
)


class ConversationNotFoundError(NotFoundError):
    code = "CONVERSATION_NOT_FOUND"
    message = "Conversation not found."

    def __init__(self, conversation_id=None):
        msg = (
            f"Conversation {conversation_id} not found."
            if conversation_id
            else self.__class__.message
        )
        super().__init__(msg, code=self.code)


class MessageNotFoundError(NotFoundError):
    code = "MESSAGE_NOT_FOUND"
    message = "Message not found."

    def __init__(self, message_id=None):
        msg = (
            f"Message {message_id} not found." if message_id else self.__class__.message
        )
        super().__init__(msg, code=self.code)


class NotAParticipantError(PermissionError):
    code = "NOT_A_PARTICIPANT"
    message = "You are not a participant in this conversation."


class NotConversationAdminError(PermissionError):
    code = "NOT_CONVERSATION_ADMIN"
    message = "Only conversation admins can perform this action."


class DirectConversationExistsError(ConflictError):
    code = "DIRECT_CONVERSATION_EXISTS"
    message = "A direct conversation already exists."

    def __init__(self, conversation_id):
        super().__init__(
            self.message,
            code=self.code,
            detail={"conversation_id": str(conversation_id)},
        )


class BlockedUserMessageError(PermissionError):
    code = "BLOCKED_USER_MESSAGE"
    message = "You cannot message a user you have blocked or who has blocked you."


class GroupConversationRequiredError(ValidationError):
    code = "GROUP_CONVERSATION_REQUIRED"
    message = "This action is only available in group conversations."


class MaxParticipantsReachedError(ValidationError):
    code = "MAX_PARTICIPANTS_REACHED"
    message = "Group conversations can have a maximum of 100 participants."


class InvalidEmojiError(ValidationError):
    code = "INVALID_EMOJI"
    message = "This emoji is not allowed as a reaction."


class MessageDeleteForbiddenError(PermissionError):
    code = "MESSAGE_DELETE_FORBIDDEN"
    message = "You can only delete your own messages."
