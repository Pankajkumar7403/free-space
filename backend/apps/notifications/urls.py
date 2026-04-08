from django.urls import path

from apps.notifications import views

app_name = "notifications"

urlpatterns = [
    # Notification list & counts
    path("", views.NotificationListView.as_view(), name="list"),
    path(
        "unread-count/",
        views.NotificationUnreadCountView.as_view(),
        name="unread-count",
    ),
    # Mark-all-read — frontend calls POST /notifications/read-all/
    path(
        "read-all/",
        views.NotificationMarkAllReadView.as_view(),
        name="read-all",
    ),
    # User preferences
    path(
        "preferences/", views.NotificationPreferenceView.as_view(), name="preferences"
    ),
    # Device tokens (FCM) — frontend calls POST/DELETE /notifications/device-token/
    path("device-token/", views.DeviceTokenView.as_view(), name="device-token"),
    # Per-notification actions — order matters: specific sub-paths before detail
    path(
        "<uuid:notification_id>/read/",
        views.NotificationMarkReadView.as_view(),
        name="mark-read",
    ),
    path(
        "<uuid:notification_id>/",
        views.NotificationDetailView.as_view(),
        name="detail",
    ),
]
