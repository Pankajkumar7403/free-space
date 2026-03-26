"""
core/middleware/security_headers.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Injects security response headers on every response.

Headers applied (OWASP hardening)
----------------------------------
  Content-Security-Policy        Prevents XSS & data injection
  X-Content-Type-Options         Prevents MIME sniffing
  X-Frame-Options                Prevents clickjacking
  Referrer-Policy                Controls referrer information leak
  Permissions-Policy             Restricts browser feature access
  Cross-Origin-Opener-Policy     Prevents cross-origin window sharing
  Cross-Origin-Embedder-Policy   Isolates cross-origin resources

Registration in settings.py MIDDLEWARE (after auth):
    "core.middleware.security_headers.SecurityHeadersMiddleware",
"""


class SecurityHeadersMiddleware:
    _CSP = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' cdn.qommunity.app; "  # tighten in M8
        "style-src  'self' 'unsafe-inline'; "
        "img-src    'self' data: cdn.qommunity.app *.amazonaws.com; "
        "media-src  'self' cdn.qommunity.app *.amazonaws.com; "
        "font-src   'self' data:; "
        "connect-src 'self' wss://api.qommunity.app sentry.io; "
        "frame-ancestors 'none'; "
        "object-src 'none'; "
        "base-uri 'self';"
    )

    _PERMISSIONS = (
        "camera=(), " "microphone=(), " "geolocation=(self), " "payment=(), " "usb=()"
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "DENY"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response["Permissions-Policy"] = self._PERMISSIONS
        response["Cross-Origin-Opener-Policy"] = "same-origin"
        response["Cross-Origin-Embedder-Policy"] = "require-corp"

        # CSP only on non-static responses
        content_type = response.get("Content-Type", "")
        if "text/html" in content_type or "application/json" in content_type:
            response["Content-Security-Policy"] = self._CSP

        # Remove information-leaking headers
        if "Server" in response:
            del response["Server"]
        if "X-Powered-By" in response:
            del response["X-Powered-By"]
        return response
