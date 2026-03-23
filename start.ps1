$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

# MinIO (S3)
$env:USE_S3                  = "True"
$env:AWS_ACCESS_KEY_ID       = "fs_admin"
$env:AWS_SECRET_ACCESS_KEY   = "fs_minio_secret"
$env:AWS_STORAGE_BUCKET_NAME = "qommunity-media"
$env:AWS_S3_ENDPOINT_URL     = "http://100.117.198.84:9000"
$env:AWS_S3_REGION_NAME      = "us-east-1"
$env:AWS_S3_CUSTOM_DOMAIN    = "100.117.198.84:9000"
$env:AWS_S3_URL_PROTOCOL     = "http://"
$env:AWS_S3_ADDRESSING_STYLE = "path"

# Mailhog
$env:EMAIL_BACKEND       = "django.core.mail.backends.smtp.EmailBackend"
$env:EMAIL_HOST          = "100.117.198.84"
$env:EMAIL_PORT          = "1025"
$env:EMAIL_HOST_USER     = ""
$env:EMAIL_HOST_PASSWORD = ""
$env:EMAIL_USE_TLS       = "False"
$env:DEFAULT_FROM_EMAIL  = "noreply@qommunity.app"

# Elasticsearch
$env:ELASTICSEARCH_URL = "http://100.117.198.84:9200"

# Celery backend/broker (same Redis DB as requested)
$env:CELERY_BROKER_URL     = "redis://:zG9QVkddWv9enkNbBAp1A2zoeHnzIG4R@100.117.198.84:6379/0"
$env:CELERY_RESULT_BACKEND = "redis://:zG9QVkddWv9enkNbBAp1A2zoeHnzIG4R@100.117.198.84:6379/0"

Set-Location backend
if (Get-Command uv -ErrorAction SilentlyContinue) {
    uv run python manage.py runserver
} else {
    python manage.py runserver
}
