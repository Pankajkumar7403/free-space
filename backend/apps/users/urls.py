# 📁 Location: backend/apps/users/urls.py
# 🔧 Include in: config/urls.py  →  path("api/v1/users/", include("apps.users.urls"))

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.users import views

app_name = "users"

urlpatterns = [
    # ── Auth ──────────────────────────────────────────────────────────────────
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
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
