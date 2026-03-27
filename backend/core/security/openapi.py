"""
OpenAPI authentication extension for drf-spectacular.
Tells spectacular how QommunityJWTAuthentication maps to OpenAPI securitySchemes.
"""

from drf_spectacular.extensions import OpenApiAuthenticationExtension


class QommunityJWTAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = "core.security.authentication.QommunityJWTAuthentication"
    name = "BearerAuth"

    def get_security_definition(self, auto_schema):
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT access token. Obtain from /api/v1/users/auth/login/",
        }
