import factory

from core.testing.factories import BaseFactory

from apps.messaging.constants import ConversationType, MessageType, ParticipantRole
from apps.messaging.models import Conversation, ConversationParticipant, Message, MessageReaction


class ConversationFactory(BaseFactory):
    class Meta:
        model = Conversation

    conversation_type = ConversationType.DIRECT
    created_by = factory.SubFactory("apps.users.tests.factories.UserFactory")
    name = ""


class ConversationParticipantFactory(BaseFactory):
    class Meta:
        model = ConversationParticipant

    conversation = factory.SubFactory(ConversationFactory)
    user = factory.SubFactory("apps.users.tests.factories.UserFactory")
    role = ParticipantRole.MEMBER


class MessageFactory(BaseFactory):
    class Meta:
        model = Message

    conversation = factory.SubFactory(ConversationFactory)
    sender = factory.SubFactory("apps.users.tests.factories.UserFactory")
    content = factory.Faker("sentence")
    message_type = MessageType.TEXT


class MessageReactionFactory(BaseFactory):
    class Meta:
        model = MessageReaction

    message = factory.SubFactory(MessageFactory)
    user = factory.SubFactory("apps.users.tests.factories.UserFactory")
    emoji = "❤️"

