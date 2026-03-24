"""
config/settings/production.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Production settings.  Import base, then override security-critical values.
Every secret MUST come from environment variables - never from code.

Run security check with:
    python manage.py check --deploy --settings=config.settings.production
"""
import logging

from .base import *   # noqa: F403

# -- Core ---------------------------------------------------------------------
DEBUG = False
SECRET_KEY = env("SECRET_KEY")   # Raises ImproperlyConfigured if missing
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")
APP_VERSION = env("APP_VERSION", default="unknown")
DJANGO_ENV = env("DJANGO_ENV", default="production")

# -- HTTPS / Cookie security (OWASP) ------------------------------------------
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31_536_000   # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

X_FRAME_OPTIONS = "DENY"

# -- Database - pgBouncer compatible ------------------------------------------
# Use CONN_MAX_AGE=0 so Django doesn't hold persistent connections;
# pgBouncer handles pooling at the proxy layer.
DATABASES = {
    "default": {
        **env.db("DATABASE_URL"),
        "CONN_MAX_AGE": 0,
        "OPTIONS": {
            "application_name": "qommunity-api",
            "connect_timeout": 5,
            "options": "-c statement_timeout=30000",  # 30s query timeout
        },
        "TEST": {"NAME": env("TEST_DATABASE_URL", default=None)},
    }
}

# -- Redis --------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_URL", default="redis://localhost:6379/0"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {"max_connections": 50},
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
            "IGNORE_EXCEPTIONS": True,
            "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
        },
        "KEY_PREFIX": "qommunity",
    }
}

# -- Celery -------------------------------------------------------------------
CELERY_BROKER_URL = env("REDIS_URL", default="redis://localhost:6379/2")
CELERY_RESULT_BACKEND = env("REDIS_URL", default="redis://localhost:6379/2")
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1   # Fair dispatch for long tasks
CELERY_TASK_ACKS_LATE = True   # Acknowledge only after completion
CELERY_TASK_REJECT_ON_WORKER_LOST = True

# -- CORS ---------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS")

# -- Email --------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="smtp.sendgrid.net")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "apikey"
EMAIL_HOST_PASSWORD = env("SENDGRID_API_KEY", default="")

# -- Sentry -------------------------------------------------------------------
SENTRY_DSN = env("SENTRY_DSN", default="")
SENTRY_TRACES_SAMPLE_RATE = env.float("SENTRY_TRACES_SAMPLE_RATE", default=0.10)
SENTRY_PROFILES_SAMPLE_RATE = env.float("SENTRY_PROFILES_SAMPLE_RATE", default=0.05)

# Bootstrap Sentry immediately
from core.monitoring.sentry import init_sentry   # noqa: E402
init_sentry(locals())

# -- Logging - structured JSON -------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s",
        },
    },
    "filters": {
        "require_debug_false": {"()": "django.utils.log.RequireDebugFalse"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": env("DJANGO_LOG_LEVEL", default="INFO"),
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": env("DJANGO_LOG_LEVEL", default="INFO"),
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": env("DB_LOG_LEVEL", default="WARNING"),
            "propagate": False,
        },
        "django.security": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}

# -- Static files --------------------------------------------------------------
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
STATIC_ROOT = "/app/staticfiles"
