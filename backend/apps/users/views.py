# 📁 Location: backend/apps/users/views.py

from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.permissions import IsOwner
from apps.users.selectors import (
    get_followers,
    get_following,
    get_user_by_id,
    get_user_by_username,
    search_users,
)
from apps.users.serializers import (
    ForgotPasswordSerializer,
    FollowSerializer,
    LoginSerializer,
    OAuthCallbackSerializer,
    OAuthInitSerializer,
    ResendVerificationEmailSerializer,
    RefreshTokenSerializer,
    RegisterSerializer,
    ResetPasswordSerializer,
    UpdateProfileSerializer,
    UserPrivateSerializer,
    UserPublicSerializer,
    VerifyEmailSerializer,
)
from apps.users.services import (
    CreateUserInput,
    UpdateProfileInput,
    accept_follow_request,
    authenticate_user,
    build_oauth_init_url,
    block_user,
    create_user,
    deactivate_user,
    follow_user,
    issue_email_verification_code,
    issue_password_reset_code,
    mute_user,
    oauth_login_or_register,
    reject_follow_request,
    reset_password_with_otp,
    unblock_user,
    unfollow_user,
    unmute_user,
    update_profile,
    verify_email_with_otp,
)
from core.pagination.cursor import CursorPagination
from core.security.jwt import blacklist_refresh_token, create_token_pair


class RegisterView(APIView):
    """POST /api/v1/users/register/"""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        user = create_user(
            CreateUserInput(
                email=d["email"],
                username=d["username"],
                password=d["password"],
            )
        )
        tokens = create_token_pair(user)
        return Response(
            {
                "user": UserPrivateSerializer(user).data,
                "tokens": tokens,
                "access": tokens["access"],
                "refresh": tokens["refresh"],
                "email_verification_sent": True,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """POST /api/v1/users/login/"""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        user = authenticate_user(email=d["email"], password=d["password"])
        tokens = create_token_pair(user)
        return Response(
            {
                "user": UserPrivateSerializer(user).data,
                "tokens": tokens,
                "access": tokens["access"],
                "refresh": tokens["refresh"],
            }
        )


class ForgotPasswordView(APIView):
    """POST /api/v1/users/forgot-password/"""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        issue_password_reset_code(email=serializer.validated_data["email"])
        # Generic success response prevents email enumeration.
        return Response({"ok": True}, status=status.HTTP_200_OK)


class ResetPasswordView(APIView):
    """POST /api/v1/users/reset-password/"""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        reset_password_with_otp(otp=d["otp"], new_password=d["new_password"])
        return Response({"ok": True}, status=status.HTTP_200_OK)


class VerifyEmailView(APIView):
    """POST /api/v1/users/verify-email/"""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get("email") or getattr(request.user, "email", "")
        if not email:
            return Response(
                {"detail": "email is required for unauthenticated verification"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        verify_email_with_otp(otp=serializer.validated_data["otp"], email=email)
        return Response({"ok": True}, status=status.HTTP_200_OK)


class ResendVerificationEmailView(APIView):
    """POST /api/v1/users/verify-email/resend/"""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = ResendVerificationEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get("email") or getattr(request.user, "email", "")
        if not email:
            return Response(
                {"detail": "email is required for unauthenticated resend"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        issue_email_verification_code(email=email)
        return Response({"ok": True}, status=status.HTTP_200_OK)


class OAuthInitView(APIView):
    """GET /api/v1/users/oauth/<provider>/init/?redirect_uri=..."""

    permission_classes = [AllowAny]

    def get(self, request: Request, provider: str) -> Response:
        serializer = OAuthInitSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        init_url = build_oauth_init_url(
            provider=provider, redirect_uri=serializer.validated_data["redirect_uri"]
        )
        return Response({"url": init_url}, status=status.HTTP_200_OK)


class OAuthCallbackView(APIView):
    """POST /api/v1/users/oauth/<provider>/"""

    permission_classes = [AllowAny]

    def post(self, request: Request, provider: str) -> Response:
        serializer = OAuthCallbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        user = oauth_login_or_register(
            provider=provider,
            code=d["code"],
            redirect_uri=d["redirect_uri"],
            state=d.get("state"),
        )
        tokens = create_token_pair(user)
        return Response(
            {
                "user": UserPrivateSerializer(user).data,
                "tokens": tokens,
                "access": tokens["access"],
                "refresh": tokens["refresh"],
            }
        )


class FaviconFallbackView(APIView):
    """
    GET /api/v1/users/favicon-16.png/ and /favicon-32.png/

    Some clients can request favicon paths relative to /users/*.
    Return 204 instead of letting username catch-all route produce 401.
    """

    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        return Response(status=status.HTTP_204_NO_CONTENT)


class LogoutView(APIView):
    """POST /api/v1/users/logout/  — blacklists the refresh token."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = RefreshTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        blacklist_refresh_token(serializer.validated_data["refresh"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserDetailView(APIView):
    """GET/PATCH/DELETE /api/v1/users/<user_id>/"""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, user_id) -> Response:
        user = get_user_by_id(user_id)
        # Own profile → full data; other → public data
        if request.user.pk == user.pk:
            return Response(UserPrivateSerializer(user).data)
        return Response(UserPublicSerializer(user).data)

    def patch(self, request: Request, user_id) -> Response:
        user = get_user_by_id(user_id)
        self.check_object_permissions(request, user)

        serializer = UpdateProfileSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        updated = update_profile(
            user_id=user_id,
            data=UpdateProfileInput(**serializer.validated_data),
        )
        return Response(UserPrivateSerializer(updated).data)

    def delete(self, request: Request, user_id) -> Response:
        user = get_user_by_id(user_id)
        self.check_object_permissions(request, user)
        deactivate_user(user_id=user_id)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_permissions(self):
        if self.request.method in ("PATCH", "DELETE"):
            return [IsAuthenticated(), IsOwner()]
        return [IsAuthenticated()]


class UserByUsernameView(APIView):
    """GET /api/v1/users/by-username/<username>/"""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, username: str) -> Response:
        user = get_user_by_username(username)
        if request.user.pk == user.pk:
            return Response(UserPrivateSerializer(user).data)
        return Response(UserPublicSerializer(user).data)


class MeView(APIView):
    """GET /api/v1/users/me/  — shortcut for own profile."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return Response(UserPrivateSerializer(request.user).data)


class UserSearchView(APIView):
    """GET /api/v1/users/search/?q=<query>"""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        query = request.query_params.get("q", "").strip()
        if len(query) < 2:
            return Response({"results": [], "pagination": {}})

        qs = search_users(query, exclude_user=request.user)
        paginator = CursorPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(
            UserPublicSerializer(page, many=True).data
        )


# ── Follow views ───────────────────────────────────────────────────────────────


class FollowView(APIView):
    """POST/DELETE /api/v1/users/<user_id>/follow/"""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request, user_id) -> Response:
        follow = follow_user(follower_id=request.user.pk, following_id=user_id)
        return Response(FollowSerializer(follow).data, status=status.HTTP_201_CREATED)

    def delete(self, request: Request, user_id) -> Response:
        unfollow_user(follower_id=request.user.pk, following_id=user_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class FollowersListView(APIView):
    """GET /api/v1/users/<user_id>/followers/"""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, user_id) -> Response:
        user = get_user_by_id(user_id)
        qs = get_followers(user)
        paginator = CursorPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(
            UserPublicSerializer(page, many=True).data
        )


class FollowingListView(APIView):
    """GET /api/v1/users/<user_id>/following/"""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, user_id) -> Response:
        user = get_user_by_id(user_id)
        qs = get_following(user)
        paginator = CursorPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(
            UserPublicSerializer(page, many=True).data
        )


class FollowRequestAcceptView(APIView):
    """POST /api/v1/users/follow-requests/<follower_id>/accept/"""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request, follower_id) -> Response:
        follow = accept_follow_request(user_id=request.user.pk, follower_id=follower_id)
        return Response(FollowSerializer(follow).data)


class FollowRequestRejectView(APIView):
    """DELETE /api/v1/users/follow-requests/<follower_id>/"""

    permission_classes = [IsAuthenticated]

    def delete(self, request: Request, follower_id) -> Response:
        reject_follow_request(user_id=request.user.pk, follower_id=follower_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Block / Mute views ────────────────────────────────────────────────────────


class BlockView(APIView):
    """POST/DELETE /api/v1/users/<user_id>/block/"""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request, user_id) -> Response:
        block_user(blocker_id=request.user.pk, blocked_id=user_id)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request: Request, user_id) -> Response:
        unblock_user(blocker_id=request.user.pk, blocked_id=user_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MuteView(APIView):
    """POST/DELETE /api/v1/users/<user_id>/mute/"""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request, user_id) -> Response:
        mute_user(muter_id=request.user.pk, muted_id=user_id)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request: Request, user_id) -> Response:
        unmute_user(muter_id=request.user.pk, muted_id=user_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Username-based social graph views ─────────────────────────────────────────
# These thin wrappers look up a user by username then delegate to existing
# service functions, matching the frontend's convention of using usernames
# instead of UUIDs in API paths.


class FollowByUsernameView(APIView):
    """
    POST   /api/v1/users/<username>/follow/  → follow the user
    DELETE /api/v1/users/<username>/follow/  → unfollow the user
    """

    permission_classes = [IsAuthenticated]

    def post(self, request: Request, username: str) -> Response:
        target = get_user_by_username(username)
        follow = follow_user(follower_id=request.user.pk, following_id=target.pk)
        return Response(FollowSerializer(follow).data, status=status.HTTP_201_CREATED)

    def delete(self, request: Request, username: str) -> Response:
        target = get_user_by_username(username)
        unfollow_user(follower_id=request.user.pk, following_id=target.pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


class FollowersByUsernameView(APIView):
    """GET /api/v1/users/<username>/followers/"""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, username: str) -> Response:
        user = get_user_by_username(username)
        qs = get_followers(user)
        paginator = CursorPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(
            UserPublicSerializer(page, many=True).data
        )


class FollowingByUsernameView(APIView):
    """GET /api/v1/users/<username>/following/"""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, username: str) -> Response:
        user = get_user_by_username(username)
        qs = get_following(user)
        paginator = CursorPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(
            UserPublicSerializer(page, many=True).data
        )


class BlockByUsernameView(APIView):
    """
    POST   /api/v1/users/<username>/block/  → block the user
    DELETE /api/v1/users/<username>/block/  → unblock the user
    """

    permission_classes = [IsAuthenticated]

    def post(self, request: Request, username: str) -> Response:
        target = get_user_by_username(username)
        block_user(blocker_id=request.user.pk, blocked_id=target.pk)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request: Request, username: str) -> Response:
        target = get_user_by_username(username)
        unblock_user(blocker_id=request.user.pk, blocked_id=target.pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MuteByUsernameView(APIView):
    """
    POST   /api/v1/users/<username>/mute/  → mute the user
    DELETE /api/v1/users/<username>/mute/  → unmute the user
    """

    permission_classes = [IsAuthenticated]

    def post(self, request: Request, username: str) -> Response:
        target = get_user_by_username(username)
        mute_user(muter_id=request.user.pk, muted_id=target.pk)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request: Request, username: str) -> Response:
        target = get_user_by_username(username)
        unmute_user(muter_id=request.user.pk, muted_id=target.pk)
        return Response(status=status.HTTP_204_NO_CONTENT)
