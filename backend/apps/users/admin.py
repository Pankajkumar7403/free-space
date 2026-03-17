# 📁 Location: backend/apps/users/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.users.models import BlockedUser, Follow, MutedUser, User, UserReport


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ("email", "username", "is_active", "is_verified", "account_privacy", "date_joined")
    list_filter   = ("is_active", "is_verified", "account_privacy", "is_staff")
    search_fields = ("email", "username", "display_name")
    ordering      = ("-date_joined",)

    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        ("Personal", {"fields": ("first_name", "last_name", "display_name", "bio", "website", "avatar")}),
        ("LGBTQ+ Identity", {"fields": (
            "pronouns", "pronouns_custom", "pronouns_visibility",
            "gender_identity", "gender_identity_custom", "gender_identity_visibility",
            "sexual_orientation", "sexual_orientation_custom", "sexual_orientation_visibility",
        )}),
        ("Privacy & Safety", {"fields": ("account_privacy", "safe_messaging_mode", "location_sharing")}),
        ("Status", {"fields": ("is_active", "is_verified", "is_staff", "is_superuser")}),
        ("Timestamps", {"fields": ("date_joined", "last_seen")}),
    )
    readonly_fields = ("date_joined", "last_seen")

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "username", "password1", "password2"),
        }),
    )


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display  = ("follower", "following", "status", "created_at")
    list_filter   = ("status",)
    search_fields = ("follower__username", "following__username")


@admin.register(BlockedUser)
class BlockedUserAdmin(admin.ModelAdmin):
    list_display  = ("blocker", "blocked", "created_at")
    search_fields = ("blocker__username", "blocked__username")


@admin.register(MutedUser)
class MutedUserAdmin(admin.ModelAdmin):
    list_display  = ("muter", "muted", "created_at")


@admin.register(UserReport)
class UserReportAdmin(admin.ModelAdmin):
    list_display  = ("reporter", "reported", "reason", "reviewed", "created_at")
    list_filter   = ("reason", "reviewed")
    actions       = ["mark_reviewed"]

    @admin.action(description="Mark selected reports as reviewed")
    def mark_reviewed(self, request, queryset):
        queryset.update(reviewed=True)