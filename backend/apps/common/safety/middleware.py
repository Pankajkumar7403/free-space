"""
apps/common/safety/middleware.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
CrisisResourceMiddleware - injects a crisis-resources header
on API responses to posts/comments that triggered the crisis filter.

The header X-Crisis-Resources: true signals the frontend to
surface the crisis resource panel for the current user.
"""


class CrisisResourceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if getattr(request, "_crisis_content_detected", False):
            response["X-Crisis-Resources"] = "true"
        return response
