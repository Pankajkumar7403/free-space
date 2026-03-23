from __future__ import annotations

import uuid
import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.selectors import (
    get_notifications_for_user,
    get_unread_notification_count,
    get_notification_preferences,
)
from apps.notifications.serializers import (
    DeviceTokenDeregisterSerializer,
    DeviceTokenRegisterSerializer,
    NotificationPreferenceSerializer,
    NotificationPreferenceUpdateSerializer,
    NotificationSerializer,
)
from apps.notifications.services import (
    delete_notification,
    deregister_device_token,
    mark_all_notifications_read,
    mark_notification_read,
    register_device_token,
    update_notification_preferences,
)
from core.pagination.cursor import CursorPagination

logger = logging.getLogger(__name__)


class NotificationListView(APIView):
    """
    GET /api/v1/notifications/
    GET /api/v1/notifications/?unread_only=true
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        unread_only = request.query_params.get("unread_only", "false").lower() == "true"
        qs = get_notifications_for_user(
            request.user.id,
            include_read=not unread_only,
        )
        paginator = CursorPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(
            NotificationSerializer(page, many=True).data
        )


class NotificationUnreadCountView(APIView):
    """GET /api/v1/notifications/unread-count/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = get_unread_notification_count(request.user.id)
        return Response({"unread_count": count})


class NotificationMarkAllReadView(APIView):
    """POST /api/v1/notifications/mark-all-read/"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        count = mark_all_notifications_read(user_id=request.user.id)
        return Response({"marked_read": count})


class NotificationDetailView(APIView):
    """
    PATCH  /api/v1/notifications/<notification_id>/   — mark as read
    DELETE /api/v1/notifications/<notification_id>/   — delete
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, notification_id: uuid.UUID):
        notification = mark_notification_read(
            notification_id=notification_id,
            user_id=request.user.id,
        )
        return Response(NotificationSerializer(notification).data)

    def delete(self, request, notification_id: uuid.UUID):
        delete_notification(
            notification_id=notification_id,
            user_id=request.user.id,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class NotificationPreferenceView(APIView):
    """
    GET   /api/v1/notifications/preferences/
    PATCH /api/v1/notifications/preferences/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        prefs = get_notification_preferences(request.user.id)
        return Response(NotificationPreferenceSerializer(prefs).data)

    def patch(self, request):
        serializer = NotificationPreferenceUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        prefs = update_notification_preferences(
            user_id=request.user.id,
            preferences=serializer.validated_data,
        )
        return Response(NotificationPreferenceSerializer(prefs).data)


class DeviceTokenView(APIView):
    """
    POST   /api/v1/notifications/device-tokens/   — register FCM token
    DELETE /api/v1/notifications/device-tokens/   — deregister FCM token
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DeviceTokenRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        token = register_device_token(
            user_id=request.user.id,
            token=d["token"],
            platform=d["platform"],
        )
        return Response({"id": str(token.id)}, status=status.HTTP_201_CREATED)

    def delete(self, request):
        serializer = DeviceTokenDeregisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        deregister_device_token(
            user_id=request.user.id,
            token=serializer.validated_data["token"],
        )
        return Response(status=status.HTTP_204_NO_CONTENT)