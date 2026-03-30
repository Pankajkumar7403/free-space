from django.urls import path

from apps.messaging import views

app_name = "messaging"

urlpatterns = [
    path(
        "conversations/", views.ConversationListView.as_view(), name="conversation-list"
    ),
    path(
        "conversations/direct/",
        views.DirectConversationView.as_view(),
        name="direct-conversation",
    ),
    path(
        "conversations/<uuid:conversation_id>/",
        views.ConversationDetailView.as_view(),
        name="conversation-detail",
    ),
    path(
        "conversations/<uuid:conversation_id>/messages/",
        views.MessageListView.as_view(),
        name="message-list",
    ),
    path(
        "conversations/<uuid:conversation_id>/read/",
        views.ConversationMarkReadView.as_view(),
        name="conversation-read",
    ),
    path(
        "conversations/<uuid:conversation_id>/participants/",
        views.ConversationParticipantsView.as_view(),
        name="conversation-participants",
    ),
    path(
        "<uuid:message_id>/", views.MessageDetailView.as_view(), name="message-detail"
    ),
    path(
        "<uuid:message_id>/reactions/",
        views.MessageReactionView.as_view(),
        name="message-reactions",
    ),
    path("unread-count/", views.UnreadCountView.as_view(), name="unread-count"),
]
