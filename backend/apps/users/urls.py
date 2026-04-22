# 📁 Location: backend/apps/users/urls.py
# 🔧 Include in: config/urls.py  →  path("api/v1/users/", include("apps.users.urls"))

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.users import views

app_name = "users"

urlpatterns = [
    # ── Favicon fallback ──────────────────────────────────────────────────────
    # Avoid 401 noise when browser resolves favicon relative to /users/* paths.
    path("favicon-16.png/", views.FaviconFallbackView.as_view(), name="favicon-16"),
    path("favicon-32.png/", views.FaviconFallbackView.as_view(), name="favicon-32"),

    # ── Auth ──────────────────────────────────────────────────────────────────
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("forgot-password/", views.ForgotPasswordView.as_view(), name="forgot-password"),
    path("reset-password/", views.ResetPasswordView.as_view(), name="reset-password"),
    path("verify-email/", views.VerifyEmailView.as_view(), name="verify-email"),
    path(
        "verify-email/resend/",
        views.ResendVerificationEmailView.as_view(),
        name="verify-email-resend",
    ),
    path("oauth/<str:provider>/init/", views.OAuthInitView.as_view(), name="oauth-init"),
    path("oauth/<str:provider>/", views.OAuthCallbackView.as_view(), name="oauth-callback"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),

    # ── Own profile ───────────────────────────────────────────────────────────
    path("me/", views.MeView.as_view(), name="me"),

    # ── Search ────────────────────────────────────────────────────────────────
    path("search/", views.UserSearchView.as_view(), name="search"),

    # ── Explicit by-username lookup (legacy / alternative) ────────────────────
    path(
        "by-username/<str:username>/",
        views.UserByUsernameView.as_view(),
        name="by-username",
    ),

    # ── Follow requests (private accounts) ───────────────────────────────────
    # Must appear before <uuid:user_id>/ and <str:username>/ catch-alls
    path(
        "follow-requests/<uuid:follower_id>/accept/",
        views.FollowRequestAcceptView.as_view(),
        name="follow-request-accept",
    ),
    path(
        "follow-requests/<uuid:follower_id>/",
        views.FollowRequestRejectView.as_view(),
        name="follow-request-reject",
    ),

    # ── UUID-based profile & social graph ────────────────────────────────────
    path("<uuid:user_id>/", views.UserDetailView.as_view(), name="detail"),
    path("<uuid:user_id>/follow/", views.FollowView.as_view(), name="follow"),
    path(
        "<uuid:user_id>/followers/",
        views.FollowersListView.as_view(),
        name="followers",
    ),
    path(
        "<uuid:user_id>/following/",
        views.FollowingListView.as_view(),
        name="following",
    ),
    path("<uuid:user_id>/block/", views.BlockView.as_view(), name="block"),
    path("<uuid:user_id>/mute/", views.MuteView.as_view(), name="mute"),

    # ── Username-based social graph (used by frontend) ────────────────────────
    # Specific sub-paths must appear before the <str:username>/ catch-all.
    path(
        "<str:username>/follow/",
        views.FollowByUsernameView.as_view(),
        name="follow-by-username",
    ),
    path(
        "<str:username>/followers/",
        views.FollowersByUsernameView.as_view(),
        name="followers-by-username",
    ),
    path(
        "<str:username>/following/",
        views.FollowingByUsernameView.as_view(),
        name="following-by-username",
    ),
    path(
        "<str:username>/block/",
        views.BlockByUsernameView.as_view(),
        name="block-by-username",
    ),
    path(
        "<str:username>/mute/",
        views.MuteByUsernameView.as_view(),
        name="mute-by-username",
    ),
    # Profile by username – catch-all, must be last
    path(
        "<str:username>/",
        views.UserByUsernameView.as_view(),
        name="profile-by-username",
    ),
]
