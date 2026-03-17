# 📁 Location: backend/apps/users/permissions.py

from rest_framework.permissions import BasePermission, IsAuthenticated


class IsOwner(BasePermission):
    """
    Allow access only if the requesting user owns the object.
    The view must set `obj` as a User instance or an object with a `user` FK.
    """
    message = "You do not have permission to modify this resource."

    def has_object_permission(self, request, view, obj) -> bool:
        # Support both: obj is a User, or obj has a .user FK
        owner = obj if hasattr(obj, "email") else getattr(obj, "user", None)
        return owner == request.user


class IsVerified(BasePermission):
    """Allow access only to email-verified users."""
    message = "Please verify your email address to perform this action."

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_verified
        )


class IsPrivateProfile(BasePermission):
    """
    Grants access only if the target user's profile is public,
    or the requester already follows them.
    Used on profile detail views.
    """

    def has_object_permission(self, request, view, obj) -> bool:
        from apps.users.constants import AccountPrivacyChoices
        from apps.users.selectors import is_following

        if obj.account_privacy == AccountPrivacyChoices.PUBLIC:
            return True
        if request.user == obj:
            return True
        if obj.account_privacy == AccountPrivacyChoices.FOLLOWERS_ONLY:
            return is_following(follower=request.user, following=obj)
        return False  # PRIVATE