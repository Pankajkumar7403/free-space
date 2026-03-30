import pytest

from apps.messaging.tests.factories import (
    ConversationFactory,
    ConversationParticipantFactory,
    MessageFactory,
    MessageReactionFactory,
)


@pytest.fixture
def conversation_factory(db):
    def _create(**kwargs):
        return ConversationFactory(**kwargs)

    return _create


@pytest.fixture
def participant_factory(db):
    def _create(**kwargs):
        return ConversationParticipantFactory(**kwargs)

    return _create


@pytest.fixture
def message_factory(db):
    def _create(**kwargs):
        return MessageFactory(**kwargs)

    return _create


@pytest.fixture
def reaction_factory(db):
    def _create(**kwargs):
        return MessageReactionFactory(**kwargs)

    return _create


@pytest.fixture
def direct_conversation(db, user_factory):
    from apps.messaging.services import create_direct_conversation

    user1 = user_factory()
    user2 = user_factory()
    conv, _ = create_direct_conversation(user1_id=user1.id, user2_id=user2.id)
    return conv, user1, user2


@pytest.fixture
def group_conversation(db, user_factory):
    from apps.messaging.services import create_group_conversation

    creator = user_factory()
    member1 = user_factory()
    member2 = user_factory()
    conv = create_group_conversation(
        creator_id=creator.id,
        participant_ids=[member1.id, member2.id],
        name="Test Group 🏳️‍🌈",
    )
    return conv, creator, member1, member2

