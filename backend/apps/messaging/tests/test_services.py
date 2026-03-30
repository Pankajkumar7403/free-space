import uuid
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError

from apps.messaging.constants import ConversationType, MessageType, ParticipantRole
from apps.messaging.exceptions import (
    BlockedUserMessageError,
    GroupConversationRequiredError,
    InvalidEmojiError,
    MaxParticipantsReachedError,
    MessageDeleteForbiddenError,
    NotAParticipantError,
    NotConversationAdminError,
)
from apps.messaging.models import ConversationParticipant, Message, MessageReaction
from apps.messaging.services import (
    add_participant,
    add_reaction,
    create_direct_conversation,
    create_group_conversation,
    delete_message,
    edit_message,
    mark_conversation_read,
    remove_participant,
    remove_reaction,
    send_message,
)


@pytest.mark.django_db
class TestCreateDirectConversation:
    def test_creates_conversation(self, user_factory):
        u1 = user_factory()
        u2 = user_factory()
        conv, created = create_direct_conversation(user1_id=u1.id, user2_id=u2.id)
        assert created is True
        assert conv.conversation_type == ConversationType.DIRECT

    def test_creates_two_participants(self, user_factory):
        u1 = user_factory()
        u2 = user_factory()
        conv, _ = create_direct_conversation(user1_id=u1.id, user2_id=u2.id)
        assert ConversationParticipant.objects.filter(conversation=conv).count() == 2

    def test_idempotent_returns_existing(self, user_factory):
        u1 = user_factory()
        u2 = user_factory()
        conv1, created1 = create_direct_conversation(user1_id=u1.id, user2_id=u2.id)
        conv2, created2 = create_direct_conversation(user1_id=u1.id, user2_id=u2.id)
        assert created1 is True
        assert created2 is False
        assert conv1.id == conv2.id

    def test_raises_if_blocked(self, user_factory):
        u1 = user_factory()
        u2 = user_factory()
        with patch("apps.common.safety.services.is_blocked", return_value=True):
            with pytest.raises(BlockedUserMessageError):
                create_direct_conversation(user1_id=u1.id, user2_id=u2.id)

    def test_creates_system_message_on_creation(self, user_factory):
        u1 = user_factory()
        u2 = user_factory()
        conv, _ = create_direct_conversation(user1_id=u1.id, user2_id=u2.id)
        sys_msgs = Message.objects.filter(
            conversation=conv, message_type=MessageType.SYSTEM
        )
        assert sys_msgs.exists()

    def test_creator_is_admin(self, user_factory):
        u1 = user_factory()
        u2 = user_factory()
        conv, _ = create_direct_conversation(user1_id=u1.id, user2_id=u2.id)
        p = ConversationParticipant.objects.get(conversation=conv, user=u1)
        assert p.role == ParticipantRole.ADMIN


@pytest.mark.django_db
class TestCreateGroupConversation:
    def test_creates_group(self, user_factory):
        creator = user_factory()
        m1 = user_factory()
        m2 = user_factory()
        conv = create_group_conversation(
            creator_id=creator.id,
            participant_ids=[m1.id, m2.id],
            name="Pride Group 🏳️‍🌈",
        )
        assert conv.conversation_type == ConversationType.GROUP
        assert conv.name == "Pride Group 🏳️‍🌈"

    def test_creator_is_admin(self, user_factory):
        creator = user_factory()
        m1 = user_factory()
        conv = create_group_conversation(
            creator_id=creator.id, participant_ids=[m1.id], name="Test Group"
        )
        p = ConversationParticipant.objects.get(conversation=conv, user=creator)
        assert p.role == ParticipantRole.ADMIN

    def test_max_participants_exceeded_raises(self, user_factory):
        creator = user_factory()
        many_ids = [uuid.uuid4() for _ in range(101)]
        with pytest.raises(MaxParticipantsReachedError):
            create_group_conversation(
                creator_id=creator.id, participant_ids=many_ids, name="Too Big"
            )


@pytest.mark.django_db
class TestSendMessage:
    def test_creates_message(self, direct_conversation):
        conv, u1, _u2 = direct_conversation
        msg = send_message(
            conversation_id=conv.id, sender_id=u1.id, content="Hello there! 🌈"
        )
        assert msg.content == "Hello there! 🌈"
        assert msg.sender_id == u1.id

    def test_non_participant_raises(self, direct_conversation, user_factory):
        conv, _u1, _u2 = direct_conversation
        outsider = user_factory()
        with pytest.raises(NotAParticipantError):
            send_message(conversation_id=conv.id, sender_id=outsider.id, content="Hi")

    def test_empty_content_raises(self, direct_conversation):
        conv, u1, _u2 = direct_conversation
        with pytest.raises(ValidationError):
            send_message(conversation_id=conv.id, sender_id=u1.id, content="")


@pytest.mark.django_db
class TestDeleteMessage:
    def test_soft_deletes_message(self, direct_conversation):
        conv, u1, _u2 = direct_conversation
        msg = send_message(conversation_id=conv.id, sender_id=u1.id, content="Hello")
        delete_message(message_id=msg.id, user_id=u1.id)
        msg.refresh_from_db()
        assert msg.is_deleted is True
        assert msg.content == ""
        assert msg.deleted_at is not None

    def test_wrong_user_raises(self, direct_conversation):
        conv, u1, u2 = direct_conversation
        msg = send_message(conversation_id=conv.id, sender_id=u1.id, content="Hello")
        with pytest.raises(MessageDeleteForbiddenError):
            delete_message(message_id=msg.id, user_id=u2.id)


@pytest.mark.django_db
class TestEditMessage:
    def test_edits_content(self, direct_conversation):
        conv, u1, _u2 = direct_conversation
        msg = send_message(conversation_id=conv.id, sender_id=u1.id, content="Original")
        edit_message(message_id=msg.id, user_id=u1.id, new_content="Edited!")
        msg.refresh_from_db()
        assert msg.content == "Edited!"
        assert msg.is_edited is True
        assert msg.edited_at is not None


@pytest.mark.django_db
class TestMarkConversationRead:
    def test_returns_1_on_success(self, direct_conversation):
        conv, u1, _u2 = direct_conversation
        count = mark_conversation_read(conversation_id=conv.id, user_id=u1.id)
        assert count == 1


@pytest.mark.django_db
class TestReactions:
    def test_add_reaction_creates_record(self, direct_conversation):
        conv, u1, u2 = direct_conversation
        msg = send_message(conversation_id=conv.id, sender_id=u1.id, content="Hello")
        add_reaction(message_id=msg.id, user_id=u2.id, emoji="❤️")
        assert MessageReaction.objects.filter(message=msg, user=u2, emoji="❤️").exists()

    def test_invalid_emoji_raises(self, direct_conversation):
        conv, u1, u2 = direct_conversation
        msg = send_message(conversation_id=conv.id, sender_id=u1.id, content="Hello")
        with pytest.raises(InvalidEmojiError):
            add_reaction(message_id=msg.id, user_id=u2.id, emoji="🦄")

    def test_remove_reaction_deletes_record(self, direct_conversation):
        conv, u1, u2 = direct_conversation
        msg = send_message(conversation_id=conv.id, sender_id=u1.id, content="Hello")
        add_reaction(message_id=msg.id, user_id=u2.id, emoji="❤️")
        remove_reaction(message_id=msg.id, user_id=u2.id, emoji="❤️")
        assert not MessageReaction.objects.filter(
            message=msg, user=u2, emoji="❤️"
        ).exists()


@pytest.mark.django_db
class TestGroupManagement:
    def test_add_participant_success(self, group_conversation, user_factory):
        conv, creator, _m1, _m2 = group_conversation
        new_user = user_factory()
        add_participant(
            conversation_id=conv.id, user_id=new_user.id, added_by_id=creator.id
        )
        assert ConversationParticipant.objects.filter(
            conversation=conv, user=new_user
        ).exists()

    def test_non_admin_cannot_add(self, group_conversation, user_factory):
        conv, _creator, m1, _m2 = group_conversation
        new_user = user_factory()
        with pytest.raises(NotConversationAdminError):
            add_participant(
                conversation_id=conv.id, user_id=new_user.id, added_by_id=m1.id
            )

    def test_direct_conversation_raises(self, direct_conversation, user_factory):
        conv, u1, _u2 = direct_conversation
        new_user = user_factory()
        with pytest.raises(GroupConversationRequiredError):
            add_participant(
                conversation_id=conv.id, user_id=new_user.id, added_by_id=u1.id
            )

    def test_remove_self_always_allowed(self, group_conversation):
        conv, _creator, m1, _m2 = group_conversation
        remove_participant(conversation_id=conv.id, user_id=m1.id, removed_by_id=m1.id)
        assert not ConversationParticipant.objects.filter(
            conversation=conv, user=m1
        ).exists()
