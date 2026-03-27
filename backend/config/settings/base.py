import os
from datetime import timedelta
from pathlib import Path

from celery.schedules import crontab
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
USE_S3 = os.getenv("USE_S3", "false").lower() == "true"

# ── Security ──────────────────────────────────────────────────────────────────

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set in environment variables.")

DEBUG = False
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")

# ── Apps ──────────────────────────────────────────────────────────────────────

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
]

THIRD_PARTY_APPS = [
    "django_prometheus",
    "channels",
    "drf_spectacular",
    "rest_framework",
    "corsheaders",
    "django_elasticsearch_dsl",
    "django_celery_beat",
    "django_celery_results",
]
if USE_S3:
    THIRD_PARTY_APPS = [*THIRD_PARTY_APPS, "storages"]

LOCAL_APPS = [
    "apps.users",
    "apps.posts",
    "apps.comments",
    "apps.likes",
    "apps.feed",
    "apps.notifications",
    "apps.media",
    "apps.common",
]

INSTALLED_APPS = ["daphne"] + DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ── Middleware (order matters) ─────────────────────────────────────────────────

MIDDLEWARE = [
    # prometheus before-middleware must be first
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    # 1. Safety net — must be first to catch everything below it
    "core.middleware.exception_handler.ExceptionHandlerMiddleware",
    # 2. Django security headers
    "django.middleware.security.SecurityMiddleware",
    # 3. CORS — must be before SessionMiddleware
    "corsheaders.middleware.CorsMiddleware",
    # 4. Security hardening headers
    "core.middleware.security_headers.SecurityHeadersMiddleware",
    # 5. Request ID injection + structured logging
    "core.middleware.request_logging.RequestLoggingMiddleware",
    # 6. Safety response header injection
    "apps.common.safety.middleware.CrisisResourceMiddleware",
    # 7. Prometheus metrics
    "core.middleware.metrics.PrometheusMetricsMiddleware",
    # 6. Standard Django middleware
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # prometheus after-middleware must be last
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ── Database ──────────────────────────────────────────────────────────────────

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "qommunity_db"),
        "USER": os.getenv("POSTGRES_USER", "qommunity_user"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "qommunity_password"),
        "HOST": os.getenv("POSTGRES_HOST", "localhost"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": 60,
        "OPTIONS": {
            "connect_timeout": 10,
        },
    }
}

# ── Cache / Redis ─────────────────────────────────────────────────────────────

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [os.getenv("REDIS_URL", "redis://localhost:6379/1")],
            # Keep channel layer traffic separate from default cache DB.
            "capacity": 1500,
            "expiry": 10,
        },
    }
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
            "IGNORE_EXCEPTIONS": True,  # cache miss on Redis error, don't crash
        },
        "KEY_PREFIX": "qommunity",
    }
}

# ── Celery ────────────────────────────────────────────────────────────────────

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TIMEZONE = os.getenv("CELERY_TIMEZONE", "Asia/Kolkata")
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_TASK_TRACK_STARTED = True
CELERY_RESULT_EXTENDED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes hard limit
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60

CELERY_BEAT_SCHEDULE = {}
CELERY_BEAT_SCHEDULE.update(
    {
        "cleanup-old-notifications": {
            "task": "apps.notifications.tasks.cleanup_old_notifications",
            "schedule": crontab(hour=3, minute=0),  # daily at 3 AM
        },
    }
)

# ── Kafka ─────────────────────────────────────────────────────────────────────

KAFKA_ENABLED = os.getenv("KAFKA_ENABLED", "false").lower() == "true"
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

# ── Elasticsearch ──────────────────────────────────────────────────────────────
ELASTICSEARCH_DSL = {
    "default": {"hosts": os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")},
}

# ── Auth ──────────────────────────────────────────────────────────────────────

AUTH_USER_MODEL = "users.User"

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# ── DRF ───────────────────────────────────────────────────────────────────────

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "core.security.authentication.QommunityJWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PAGINATION_CLASS": "core.pagination.cursor.CursorPagination",
    "PAGE_SIZE": 20,
    "EXCEPTION_HANDLER": "core.exceptions.handler.custom_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
    },
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Qommunity API",
    "DESCRIPTION": (
        "Production-grade social media platform designed exclusively for the "
        "LGBTQ+ community. Built with pride. Engineered for safety. 🏳️‍🌈"
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SORT_OPERATIONS": False,
    "CONTACT": {
        "name": "Qommunity Engineering",
        "email": "engineering@qommunity.app",
    },
    "LICENSE": {"name": "Proprietary"},
    "SERVERS": [{"url": "https://api.qommunity.app", "description": "Production"}],
    "TAGS": [
        {"name": "auth", "description": "Authentication & authorization"},
        {"name": "users", "description": "User profiles & social graph"},
        {"name": "posts", "description": "Post CRUD & hashtags"},
        {"name": "feed", "description": "Home feed & explore"},
        {"name": "media", "description": "Image & video upload pipeline"},
        {"name": "notifications", "description": "Real-time & push notifications"},
        {"name": "gdpr", "description": "GDPR data portability & erasure"},
    ],
    "PREPROCESSING_HOOKS": [
        "drf_spectacular.hooks.preprocess_exclude_path_format",
    ],
    "POSTPROCESSING_HOOKS": [
        "drf_spectacular.hooks.postprocess_schema_enums",
    ],
    # Reduce noise for APIViews where spectacular can't infer serializer_class.
    "COMPONENT_NO_READ_SERIALIZER_WARNING": True,
}

# ── CORS ──────────────────────────────────────────────────────────────────────

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:8000",
    ).split(",")
    if origin.strip()
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "x-app-version",
]

# ── Prometheus ───────────────────────────────────────────────────────────────
PROMETHEUS_EXPORT_MIGRATIONS = False

# ── App version (used in health check + Sentry) ─────────────────────────────
APP_VERSION = os.getenv("APP_VERSION", "0.0.1")

# ── Moderation ───────────────────────────────────────────────────────────────
MODERATION_BLOCKLIST_PATH = os.getenv("MODERATION_BLOCKLIST_PATH", "")
MODERATION_BLOCKLIST = [
    term.strip()
    for term in os.getenv("MODERATION_BLOCKLIST", "").split(",")
    if term.strip()
]
NSFW_CLASSIFIER_BACKEND = os.getenv("NSFW_CLASSIFIER_BACKEND", "stub")

# ── Internationalisation ──────────────────────────────────────────────────────

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ── Static / Media ────────────────────────────────────────────────────────────

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_ROOT = BASE_DIR / "mediafiles"

if USE_S3:
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME", "")
    AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME", "us-east-1")
    AWS_S3_ENDPOINT_URL = os.getenv("AWS_S3_ENDPOINT_URL", "")
    AWS_S3_CUSTOM_DOMAIN = os.getenv("AWS_S3_CUSTOM_DOMAIN", "")
    AWS_S3_ADDRESSING_STYLE = os.getenv("AWS_S3_ADDRESSING_STYLE", "path")
    AWS_S3_SIGNATURE_VERSION = "s3v4"
    AWS_DEFAULT_ACL = os.getenv("AWS_DEFAULT_ACL", "public-read")
    AWS_S3_FILE_OVERWRITE = False
    AWS_QUERYSTRING_AUTH = os.getenv("AWS_QUERYSTRING_AUTH", "false").lower() == "true"
    _protocol = os.getenv("AWS_S3_URL_PROTOCOL", "http://")
    if not _protocol.endswith("//"):
        _protocol = _protocol.rstrip("/") + "://"
    if AWS_S3_CUSTOM_DOMAIN and AWS_STORAGE_BUCKET_NAME:
        MEDIA_URL = f"{_protocol}{AWS_S3_CUSTOM_DOMAIN}/{AWS_STORAGE_BUCKET_NAME}/"
    elif AWS_S3_ENDPOINT_URL and AWS_STORAGE_BUCKET_NAME:
        MEDIA_URL = f"{AWS_S3_ENDPOINT_URL.rstrip('/')}/{AWS_STORAGE_BUCKET_NAME}/"
    else:
        MEDIA_URL = "/media/"
else:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
    MEDIA_URL = "/media/"

# ── Email ─────────────────────────────────────────────────────────────────────
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = os.getenv("EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "25"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "false").lower() == "true"
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@qommunity.app")
EMAIL_SENDER_NAME = "Qommunity"

# ── FCM (Firebase Cloud Messaging) ───────────────────────────────────────────
FCM_SERVER_KEY = os.getenv("FCM_SERVER_KEY", default="")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── Logging ───────────────────────────────────────────────────────────────────

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
        },
        "simple": {
            "format": "%(levelname)s %(name)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "qommunity": {"handlers": ["console"], "level": "DEBUG", "propagate": False},
    },
}

# ── App version enforcement ───────────────────────────────────────────────────

APP_MIN_VERSION = os.getenv("APP_MIN_VERSION", "1.0.0")
