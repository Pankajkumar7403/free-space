import uuid

import pytest

from apps.messaging.constants import ConversationType, ParticipantRole
from apps.messaging.models import ConversationParticipant, MessageReaction


@pytest.mark.django_db
class TestConversationModel:
    def test_uuid_primary_key(self, conversation_factory, user_factory):
        conv = conversation_factory(created_by=user_factory())
        assert isinstance(conv.id, uuid.UUID)

    def test_str_direct_conversation(self, conversation_factory, user_factory):
        conv = conversation_factory(
            conversation_type=ConversationType.DIRECT, created_by=user_factory()
        )
        assert "Direct" in str(conv)

    def test_str_group_conversation(self, conversation_factory, user_factory):
        conv = conversation_factory(
            conversation_type=ConversationType.GROUP,
            name="Pride Chat",
            created_by=user_factory(),
        )
        assert "Group" in str(conv) or "Pride Chat" in str(conv)

    def test_is_direct_property(self, conversation_factory, user_factory):
        conv = conversation_factory(
            conversation_type=ConversationType.DIRECT, created_by=user_factory()
        )
        assert conv.is_direct is True
        assert conv.is_group is False

    def test_is_group_property(self, conversation_factory, user_factory):
        conv = conversation_factory(
            conversation_type=ConversationType.GROUP,
            name="Group",
            created_by=user_factory(),
        )
        assert conv.is_group is True
        assert conv.is_direct is False


@pytest.mark.django_db
class TestConversationParticipantModel:
    def test_unique_together_user_conversation(
        self, conversation_factory, user_factory, participant_factory
    ):
        user = user_factory()
        conv = conversation_factory(created_by=user)
        participant_factory(conversation=conv, user=user)
        with pytest.raises(Exception):
            ConversationParticipant.objects.create(
                conversation=conv, user=user, role=ParticipantRole.MEMBER
            )

    def test_default_role_is_member(self, conversation_factory, user_factory):
        conv = conversation_factory(created_by=user_factory())
        user = user_factory()
        p = ConversationParticipant.objects.create(conversation=conv, user=user)
        assert p.role == ParticipantRole.MEMBER


@pytest.mark.django_db
class TestMessageReactionModel:
    def test_unique_together_message_user_emoji(
        self, reaction_factory, message_factory, conversation_factory, user_factory
    ):
        msg = message_factory(
            conversation=conversation_factory(created_by=user_factory()),
            sender=user_factory(),
        )
        user = user_factory()
        reaction_factory(message=msg, user=user, emoji="❤️")
        with pytest.raises(Exception):
            MessageReaction.objects.create(message=msg, user=user, emoji="❤️")
