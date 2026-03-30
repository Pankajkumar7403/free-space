import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("posts", "0002_search_trigger"),
    ]

    operations = [
        migrations.CreateModel(
            name="Conversation",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_deleted", models.BooleanField(db_index=True, default=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                (
                    "conversation_type",
                    models.CharField(
                        choices=[("direct", "Direct Message"), ("group", "Group Chat")],
                        db_index=True,
                        default="direct",
                        max_length=10,
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        blank=True,
                        help_text="Group name — empty for direct conversations.",
                        max_length=100,
                    ),
                ),
                ("last_message_preview", models.CharField(blank=True, max_length=100)),
                ("last_message_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_conversations",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "last_message_sender",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"db_table": "conversations", "ordering": ["-last_message_at"]},
        ),
        migrations.AddIndex(
            model_name="conversation",
            index=models.Index(fields=["-last_message_at"], name="conv_last_msg_idx"),
        ),
        migrations.CreateModel(
            name="Message",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_deleted", models.BooleanField(db_index=True, default=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("content", models.TextField(blank=True, max_length=5000)),
                (
                    "message_type",
                    models.CharField(
                        choices=[("text", "Text"), ("media", "Media Attachment"), ("system", "System Event")],
                        db_index=True,
                        default="text",
                        max_length=10,
                    ),
                ),
                ("is_edited", models.BooleanField(default=False)),
                ("edited_at", models.DateTimeField(blank=True, null=True)),
                (
                    "conversation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="messages",
                        to="messaging.conversation",
                    ),
                ),
                (
                    "sender",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="sent_messages",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "media",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="message_attachments",
                        to="posts.media",
                    ),
                ),
                (
                    "reply_to",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="replies",
                        to="messaging.message",
                    ),
                ),
            ],
            options={"db_table": "messages", "ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="message",
            index=models.Index(fields=["conversation", "-created_at"], name="msg_conv_created_idx"),
        ),
        migrations.CreateModel(
            name="ConversationParticipant",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_deleted", models.BooleanField(db_index=True, default=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("role", models.CharField(choices=[("admin", "Admin"), ("member", "Member")], default="member", max_length=10)),
                ("joined_at", models.DateTimeField(auto_now_add=True)),
                ("last_seen_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("is_muted", models.BooleanField(default=False)),
                ("is_archived", models.BooleanField(default=False)),
                (
                    "conversation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="participants",
                        to="messaging.conversation",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="conversation_participants",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"db_table": "conversation_participants"},
        ),
        migrations.AlterUniqueTogether(
            name="conversationparticipant",
            unique_together={("conversation", "user")},
        ),
        migrations.CreateModel(
            name="MessageReaction",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_deleted", models.BooleanField(db_index=True, default=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("emoji", models.CharField(max_length=10)),
                (
                    "message",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reactions",
                        to="messaging.message",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="message_reactions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"db_table": "message_reactions"},
        ),
        migrations.AlterUniqueTogether(
            name="messagereaction",
            unique_together={("message", "user", "emoji")},
        ),
        migrations.AddIndex(
            model_name="messagereaction",
            index=models.Index(fields=["message"], name="reaction_message_idx"),
        ),
    ]

