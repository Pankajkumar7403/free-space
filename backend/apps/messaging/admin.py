from django.contrib import admin

from apps.messaging.models import (
    Conversation,
    ConversationParticipant,
    Message,
    MessageReaction,
)


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ["id", "conversation_type", "name", "last_message_at", "created_by"]
    list_filter = ["conversation_type"]
    search_fields = ["name", "created_by__username"]
    readonly_fields = ["id", "created_at", "updated_at"]
    raw_id_fields = ["created_by", "last_message_sender"]


@admin.register(ConversationParticipant)
class ConversationParticipantAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "conversation", "role", "is_muted", "joined_at"]
    list_filter = ["role", "is_muted"]
    search_fields = ["user__username"]
    raw_id_fields = ["user", "conversation"]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "sender",
        "conversation",
        "message_type",
        "is_deleted",
        "created_at",
    ]
    list_filter = ["message_type", "is_deleted"]
    search_fields = ["sender__username", "content"]
    raw_id_fields = ["sender", "conversation", "reply_to", "media"]
    readonly_fields = ["id", "created_at", "updated_at", "deleted_at"]


@admin.register(MessageReaction)
class MessageReactionAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "message", "emoji", "created_at"]
    search_fields = ["user__username", "emoji"]
    raw_id_fields = ["user", "message"]
