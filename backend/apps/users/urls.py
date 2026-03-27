# 📁 Location: backend/apps/users/urls.py
# 🔧 Include in: config/urls.py  →  path("api/v1/users/", include("apps.users.urls"))

from django.urls import path

from apps.users import views

app_name = "users"

urlpatterns = [
    # ── Auth ──────────────────────────────────────────────────────────────────
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("me/", views.MeView.as_view(), name="me"),
    # ── Profile ───────────────────────────────────────────────────────────────
    path("search/", views.UserSearchView.as_view(), name="search"),
    path(
        "by-username/<str:username>/",
        views.UserByUsernameView.as_view(),
        name="by-username",
    ),
    path("<uuid:user_id>/", views.UserDetailView.as_view(), name="detail"),
    # ── Follow ────────────────────────────────────────────────────────────────
    path("<uuid:user_id>/follow/", views.FollowView.as_view(), name="follow"),
    path("<uuid:user_id>/follow/", views.UnfollowView.as_view(), name="unfollow"),
    path(
        "<uuid:user_id>/followers/", views.FollowersListView.as_view(), name="followers"
    ),
    path(
        "<uuid:user_id>/following/", views.FollowingListView.as_view(), name="following"
    ),
    # ── Follow requests (private accounts) ───────────────────────────────────
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
    # ── Block / Mute ──────────────────────────────────────────────────────────
    path("<uuid:user_id>/block/", views.BlockView.as_view(), name="block"),
    path("<uuid:user_id>/mute/", views.MuteView.as_view(), name="mute"),
]
