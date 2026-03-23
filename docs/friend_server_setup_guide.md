# Friend Setup Guide (Laptop + Spare Server)

This guide helps you run the `free-space` backend from a laptop while using services hosted on the spare computer.

---

## 1) Architecture in Simple Words

- Spare computer runs Docker containers (database, cache, storage, search, dashboards).
- Laptop runs Django app code (`runserver`).
- Laptop talks to spare computer over Tailscale.
- Data is shared because services are centralized on spare computer.

Spare server Tailscale IP: `100.117.198.84`

---

## 2) Service Endpoints (Spare Computer)

### Core services used by Django

- PostgreSQL: `100.117.198.84:5433`
- Redis: `100.117.198.84:6379`
- MinIO S3 API: `http://100.117.198.84:9000`
- Mailhog SMTP: `100.117.198.84:1025`
- Elasticsearch: `http://100.117.198.84:9200`
- Kafka broker (currently disabled in app env): `100.117.198.84:9092`

### Dashboards/UIs

- Kafka UI: `http://100.117.198.84:8080`
- MinIO Console: `http://100.117.198.84:9001`
- Mailhog Inbox: `http://100.117.198.84:8025`
- Prometheus: `http://100.117.198.84:9090`
- Grafana: `http://100.117.198.84:3000`
- Kibana: `http://100.117.198.84:5601`
- Flower: `http://100.117.198.84:5555`

---

## 3) One-Time Prerequisites on Friend Laptop

Install:

- Tailscale
- Python 3.12+
- `uv`
- Git (if cloning)

Then:

1. Open Tailscale.
2. Sign in.
3. Click **Connect**.
4. Enable **Run at startup** and **Start with Windows**.

---

## 4) Project and Environment

1. Get the same project folder.
2. Open `free-space/backend/.env`.
3. Put these values (same as your working setup):

```env
SECRET_KEY=replace-with-random-secret
ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_SETTINGS_MODULE=config.settings.development

POSTGRES_DB=fs_db
POSTGRES_USER=fs_user
POSTGRES_PASSWORD=7FV3udRk9Fqq_GgZk78bP_IQ0-W8NixE
POSTGRES_HOST=100.117.198.84
POSTGRES_PORT=5433

REDIS_URL=redis://:zG9QVkddWv9enkNbBAp1A2zoeHnzIG4R@100.117.198.84:6379/0
CELERY_BROKER_URL=redis://:zG9QVkddWv9enkNbBAp1A2zoeHnzIG4R@100.117.198.84:6379/0
CELERY_RESULT_BACKEND=redis://:zG9QVkddWv9enkNbBAp1A2zoeHnzIG4R@100.117.198.84:6379/0

KAFKA_ENABLED=false
KAFKA_BOOTSTRAP_SERVERS=100.117.198.84:9092

CORS_ALLOWED_ORIGINS=http://localhost:8000

USE_S3=True
AWS_ACCESS_KEY_ID=fs_admin
AWS_SECRET_ACCESS_KEY=fs_minio_secret
AWS_STORAGE_BUCKET_NAME=qommunity-media
AWS_S3_ENDPOINT_URL=http://100.117.198.84:9000
AWS_S3_REGION_NAME=us-east-1
AWS_S3_CUSTOM_DOMAIN=100.117.198.84:9000
AWS_S3_URL_PROTOCOL=http://
AWS_S3_ADDRESSING_STYLE=path
AWS_DEFAULT_ACL=public-read
AWS_QUERYSTRING_AUTH=false

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=100.117.198.84
EMAIL_PORT=1025
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_USE_TLS=False
DEFAULT_FROM_EMAIL=noreply@qommunity.app

ELASTICSEARCH_URL=http://100.117.198.84:9200
```

---

## 5) First Run on Friend Laptop

From `free-space/backend`:

```powershell
uv sync
uv run python manage.py migrate
uv run python manage.py runserver
```

Open:

- `http://127.0.0.1:8000`

If this opens, setup is complete.

---

## 6) Daily Morning Routine (Very Simple)

### On spare computer

```powershell
docker compose up -d
docker compose ps
```

### On laptop

1. Ensure Tailscale is connected.
2. From `free-space/backend` run:

```powershell
uv run python manage.py migrate
uv run python manage.py runserver
```

That is enough for normal development.

---

## 7) Quick Health Check Links

Open these from laptop:

- App: `http://127.0.0.1:8000`
- Metrics: `http://127.0.0.1:8000/metrics`
- Kafka UI: `http://100.117.198.84:8080`
- MinIO: `http://100.117.198.84:9001`
- Mailhog: `http://100.117.198.84:8025`
- Prometheus: `http://100.117.198.84:9090/-/healthy`
- Grafana: `http://100.117.198.84:3000/login`
- Kibana: `http://100.117.198.84:5601`

---

## 8) Common Problems and Fixes

- `could not connect to server 100.117.198.84`  
  -> Tailscale is disconnected on laptop or spare server.

- `start.ps1 not recognized`  
  -> Run it from `free-space` folder (`.\start.ps1`) or use `..\start.ps1` from backend.

- `No migrations to apply`  
  -> Good. Database schema is already up to date.

- MinIO upload fails  
  -> Check bucket `qommunity-media` exists in MinIO console.

---

## 9) What You Don’t Need to Worry About

- Running Postgres/Redis/Kafka locally on laptop.
- Creating DB schema manually every day.
- Service ports changing (they are fixed above unless server config changes).

You only need:

1. Tailscale connected.
2. Spare computer containers up.
3. Laptop `runserver` running.

