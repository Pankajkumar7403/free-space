from django.urls import path
from apps.notifications import views

app_name = "notifications"

urlpatterns = [
    # Notification list & counts
    path("",                  views.NotificationListView.as_view(),        name="list"),
    path("unread-count/",     views.NotificationUnreadCountView.as_view(), name="unread-count"),
    path("mark-all-read/",    views.NotificationMarkAllReadView.as_view(), name="mark-all-read"),

    # Per-notification actions
    path("<uuid:notification_id>/", views.NotificationDetailView.as_view(), name="detail"),

    # User preferences
    path("preferences/",      views.NotificationPreferenceView.as_view(), name="preferences"),

    # Device tokens (FCM)
    path("device-tokens/",    views.DeviceTokenView.as_view(),            name="device-tokens"),
]