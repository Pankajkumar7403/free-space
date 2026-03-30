from __future__ import annotations

import logging
import uuid

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.messaging.exceptions import NotAParticipantError
from apps.messaging.selectors import (
    get_conversation_by_id,
    get_conversation_messages,
    get_participant,
    get_unread_message_count,
    get_user_conversations,
)
from apps.messaging.serializers import (
    AddParticipantSerializer,
    AddReactionSerializer,
    ConversationSerializer,
    CreateDirectConversationSerializer,
    CreateGroupConversationSerializer,
    EditMessageSerializer,
    MessageSerializer,
    SendMessageSerializer,
)
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
from core.pagination.cursor import CursorPagination

logger = logging.getLogger(__name__)


class ConversationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = get_user_conversations(request.user.id)
        paginator = CursorPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(
            ConversationSerializer(page, many=True, context={"request": request}).data
        )

    def post(self, request):
        serializer = CreateGroupConversationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        conversation = create_group_conversation(
            creator_id=request.user.id,
            participant_ids=[uuid.UUID(str(uid)) for uid in d["participant_ids"]],
            name=d["name"],
        )
        return Response(
            ConversationSerializer(conversation, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class DirectConversationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateDirectConversationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        conversation, created = create_direct_conversation(
            user1_id=request.user.id,
            user2_id=serializer.validated_data["target_user_id"],
        )
        return Response(
            ConversationSerializer(conversation, context={"request": request}).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class ConversationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_verified_conversation(self, conversation_id, user_id):
        conversation = get_conversation_by_id(conversation_id)
        if not get_participant(conversation_id, user_id):
            raise NotAParticipantError()
        return conversation

    def get(self, request, conversation_id: uuid.UUID):
        conversation = self._get_verified_conversation(conversation_id, request.user.id)
        return Response(ConversationSerializer(conversation, context={"request": request}).data)

    def delete(self, request, conversation_id: uuid.UUID):
        self._get_verified_conversation(conversation_id, request.user.id)
        remove_participant(
            conversation_id=conversation_id,
            user_id=request.user.id,
            removed_by_id=request.user.id,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class MessageListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, conversation_id: uuid.UUID):
        if not get_participant(conversation_id, request.user.id):
            raise NotAParticipantError()

        before_id = request.query_params.get("before_id")
        qs = get_conversation_messages(
            conversation_id,
            before_id=uuid.UUID(before_id) if before_id else None,
        )
        paginator = CursorPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(MessageSerializer(page, many=True).data)

    def post(self, request, conversation_id: uuid.UUID):
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        message = send_message(
            conversation_id=conversation_id,
            sender_id=request.user.id,
            content=d.get("content", ""),
            media_id=d.get("media_id"),
            reply_to_id=d.get("reply_to_id"),
        )

        _dispatch_new_message(message)

        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)


class MessageDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, message_id: uuid.UUID):
        serializer = EditMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = edit_message(
            message_id=message_id,
            user_id=request.user.id,
            new_content=serializer.validated_data["content"],
        )
        return Response(MessageSerializer(message).data)

    def delete(self, request, message_id: uuid.UUID):
        msg = delete_message(message_id=message_id, user_id=request.user.id)
        _dispatch_delete_message(msg)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MessageReactionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, message_id: uuid.UUID):
        serializer = AddReactionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        add_reaction(
            message_id=message_id,
            user_id=request.user.id,
            emoji=serializer.validated_data["emoji"],
        )
        return Response({"emoji": serializer.validated_data["emoji"]}, status=status.HTTP_201_CREATED)

    def delete(self, request, message_id: uuid.UUID):
        serializer = AddReactionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        remove_reaction(
            message_id=message_id,
            user_id=request.user.id,
            emoji=serializer.validated_data["emoji"],
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class ConversationMarkReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, conversation_id: uuid.UUID):
        count = mark_conversation_read(conversation_id=conversation_id, user_id=request.user.id)
        return Response({"marked_read": count})


class UnreadCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = get_unread_message_count(request.user.id)
        return Response({"unread_count": count})


class ConversationParticipantsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, conversation_id: uuid.UUID):
        serializer = AddParticipantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        add_participant(
            conversation_id=conversation_id,
            user_id=serializer.validated_data["user_id"],
            added_by_id=request.user.id,
        )
        return Response(status=status.HTTP_201_CREATED)

    def delete(self, request, conversation_id: uuid.UUID):
        serializer = AddParticipantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        remove_participant(
            conversation_id=conversation_id,
            user_id=serializer.validated_data["user_id"],
            removed_by_id=request.user.id,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


def _dispatch_new_message(message) -> None:
    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer

        from apps.messaging.constants import get_conversation_group

        channel_layer = get_channel_layer()
        if channel_layer is None:
            return

        async_to_sync(channel_layer.group_send)(
            get_conversation_group(message.conversation_id),
            {"type": "message_new", "data": MessageSerializer(message).data},
        )
    except Exception as exc:
        logger.warning("messaging.ws_dispatch_failed", extra={"error": str(exc)})


def _dispatch_delete_message(message) -> None:
    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer

        from apps.messaging.constants import get_conversation_group

        channel_layer = get_channel_layer()
        if channel_layer is None:
            return

        async_to_sync(channel_layer.group_send)(
            get_conversation_group(message.conversation_id),
            {
                "type": "message_deleted",
                "data": {"type": "message_deleted", "message_id": str(message.id)},
            },
        )
    except Exception as exc:
        logger.warning("messaging.delete_dispatch_failed", extra={"error": str(exc)})

