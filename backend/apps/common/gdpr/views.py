from __future__ import annotations

import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.gdpr.serializers import (
    GDPRDeleteAccountSerializer,
    GDPRExportRequestSerializer,
)
from apps.common.gdpr.services import delete_account, request_data_export

logger = logging.getLogger(__name__)


class GDPRDataExportView(APIView):
    """
    POST /api/v1/gdpr/export/
    Request a full data export.  The ZIP is generated async and emailed.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = GDPRExportRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        job_id = request_data_export(user_id=request.user.id)
        return Response(
            {
                "message": "Your data export has been requested. "
                "You will receive an email when it is ready (up to 30 minutes).",
                "job_id": job_id,
            },
            status=status.HTTP_202_ACCEPTED,
        )


class GDPRDeleteAccountView(APIView):
    """
    DELETE /api/v1/gdpr/delete-account/
    Permanently delete account and all associated data.
    """

    permission_classes = [IsAuthenticated]

    def delete(self, request):
        serializer = GDPRDeleteAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Verify password
        if not request.user.check_password(serializer.validated_data["password"]):
            return Response(
                {
                    "error_code": "INVALID_CREDENTIALS",
                    "message": "Password is incorrect.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_id = request.user.id
        delete_account(user_id=user_id)

        logger.info("gdpr.account_deleted", extra={"user_id": str(user_id)})
        return Response(
            {
                "message": "Your account and all associated data have been permanently deleted."
            },
            status=status.HTTP_200_OK,
        )
