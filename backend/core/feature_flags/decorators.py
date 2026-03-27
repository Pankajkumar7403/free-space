"""
Decorator to gate a view or function behind a feature flag.

Usage
-----
    from core.feature_flags.decorators import require_feature

    @require_feature("graphql_relay")
    def my_view(request):
        ...

    # Per-user check
    @require_feature("new_feed_algo", user_attr="user")
    def feed_view(request):
        ...
"""

from __future__ import annotations

import functools

from django.http import JsonResponse


def require_feature(
    flag_name: str,
    user_attr: str = "user",
    fallback_status: int = 404,
):
    """
    Decorator factory.
    If the flag is disabled for the requesting user, returns fallback_status.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            from core.feature_flags.client import is_enabled

            # args[0] is `self` for class methods or `request` for functions
            request = args[0] if not hasattr(args[0], "request") else args[0].request
            user = getattr(request, user_attr, None)
            user_id = getattr(user, "id", None) if user else None

            if not is_enabled(flag_name, user_id=user_id):
                return JsonResponse(
                    {
                        "error_code": "FEATURE_NOT_AVAILABLE",
                        "message": "This feature is not yet available.",
                    },
                    status=fallback_status,
                )
            return func(*args, **kwargs)

        return wrapper

    return decorator
