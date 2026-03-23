import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        # -- Notification --------------------------------------------------------
        migrations.CreateModel(
            name="Notification",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_deleted", models.BooleanField(db_index=True, default=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                (
                    "notification_type",
                    models.CharField(
                        db_index=True,
                        max_length=30,
                        choices=[
                            ("like_post", "Liked your post"),
                            ("like_comment", "Liked your comment"),
                            ("comment", "Commented on your post"),
                            ("comment_reply", "Replied to your comment"),
                            ("follow", "Started following you"),
                            ("mention", "Mentioned you"),
                        ],
                    ),
                ),
                ("object_id", models.UUIDField(blank=True, null=True)),
                ("is_read", models.BooleanField(db_index=True, default=False)),
                ("read_at", models.DateTimeField(blank=True, null=True)),
                ("message", models.CharField(default="", max_length=255)),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="actor_notifications",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "content_type",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="contenttypes.contenttype",
                    ),
                ),
                (
                    "recipient",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notifications",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"db_table": "notifications", "ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="notification",
            index=models.Index(
                fields=["recipient", "-created_at"],
                name="notif_recipient_created_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="notification",
            index=models.Index(
                fields=["recipient", "is_read"],
                name="notif_recipient_read_idx",
            ),
        ),
        # -- NotificationPreference ---------------------------------------------
        migrations.CreateModel(
            name="NotificationPreference",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_deleted", models.BooleanField(db_index=True, default=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("likes_in_app", models.BooleanField(default=True)),
                ("likes_push", models.BooleanField(default=True)),
                ("likes_email", models.BooleanField(default=False)),
                ("comments_in_app", models.BooleanField(default=True)),
                ("comments_push", models.BooleanField(default=True)),
                ("comments_email", models.BooleanField(default=False)),
                ("follows_in_app", models.BooleanField(default=True)),
                ("follows_push", models.BooleanField(default=True)),
                ("follows_email", models.BooleanField(default=True)),
                ("mentions_in_app", models.BooleanField(default=True)),
                ("mentions_push", models.BooleanField(default=True)),
                ("mentions_email", models.BooleanField(default=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notification_preferences",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"db_table": "notification_preferences"},
        ),
        # -- DeviceToken ---------------------------------------------------------
        migrations.CreateModel(
            name="DeviceToken",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_deleted", models.BooleanField(db_index=True, default=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("token", models.CharField(db_index=True, max_length=512)),
                (
                    "platform",
                    models.CharField(
                        choices=[("ios", "iOS"), ("android", "Android"), ("web", "Web (PWA)")],
                        default="ios",
                        max_length=10,
                    ),
                ),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                (
                    "user",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="device_tokens",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"db_table": "device_tokens"},
        ),
        migrations.AlterUniqueTogether(
            name="devicetoken",
            unique_together={("user", "token")},
        ),
        migrations.AddIndex(
            model_name="devicetoken",
            index=models.Index(
                fields=["user", "is_active"],
                name="device_token_user_active_idx",
            ),
        ),
    ]
