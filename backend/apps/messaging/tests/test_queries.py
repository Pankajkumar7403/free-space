import uuid

import pytest

from apps.messaging.exceptions import ConversationNotFoundError
from apps.messaging.selectors import (
    get_conversation_by_id,
    get_conversation_messages,
    get_message_reactions_summary,
    get_unread_count_per_conversation,
    get_user_conversations,
)
from apps.messaging.services import add_reaction, mark_conversation_read, send_message


@pytest.mark.django_db
class TestGetConversationById:
    def test_returns_conversation(self, direct_conversation):
        conv, _u1, _u2 = direct_conversation
        result = get_conversation_by_id(conv.id)
        assert result.id == conv.id

    def test_raises_not_found_for_unknown(self):
        with pytest.raises(ConversationNotFoundError):
            get_conversation_by_id(uuid.uuid4())


@pytest.mark.django_db
class TestGetUserConversations:
    def test_returns_only_user_conversations(self, user_factory):
        from apps.messaging.services import create_direct_conversation

        u1 = user_factory()
        u2 = user_factory()
        u3 = user_factory()
        create_direct_conversation(user1_id=u1.id, user2_id=u2.id)
        create_direct_conversation(user1_id=u2.id, user2_id=u3.id)

        results = get_user_conversations(u1.id)
        conv_ids = set(results.values_list("id", flat=True))
        assert len(conv_ids) == 1


@pytest.mark.django_db
class TestGetConversationMessages:
    def test_returns_messages_for_conversation(self, direct_conversation):
        conv, u1, u2 = direct_conversation
        send_message(conversation_id=conv.id, sender_id=u1.id, content="Msg 1")
        send_message(conversation_id=conv.id, sender_id=u2.id, content="Msg 2")
        text_msgs = get_conversation_messages(conv.id).filter(message_type="text")
        assert text_msgs.count() == 2


@pytest.mark.django_db
class TestGetUnreadCountPerConversation:
    def test_unread_messages_counted(self, direct_conversation):
        conv, u1, u2 = direct_conversation
        send_message(conversation_id=conv.id, sender_id=u1.id, content="Msg 1")
        send_message(conversation_id=conv.id, sender_id=u1.id, content="Msg 2")
        count = get_unread_count_per_conversation(u2.id, conv.id)
        assert count == 2

    def test_after_mark_read_count_is_zero(self, direct_conversation):
        conv, u1, u2 = direct_conversation
        send_message(conversation_id=conv.id, sender_id=u1.id, content="Hello")
        mark_conversation_read(conversation_id=conv.id, user_id=u2.id)
        count = get_unread_count_per_conversation(u2.id, conv.id)
        assert count == 0


@pytest.mark.django_db
class TestGetMessageReactionsSummary:
    def test_returns_emoji_counts(self, direct_conversation):
        conv, u1, u2 = direct_conversation
        msg = send_message(conversation_id=conv.id, sender_id=u1.id, content="Hello")
        add_reaction(message_id=msg.id, user_id=u2.id, emoji="❤️")
        summary = get_message_reactions_summary(msg.id)
        assert summary["❤️"] == 1
