# 🏳️‍🌈 Qommunity Backend — Setup, Run & Test Guide

## 1. EXACT FOLDER STRUCTURE (where every file goes)

```
backend/                                ← your project root
│
├── manage.py                           ← already exists
├── pyproject.toml                      ← from session 1
├── Makefile                            ← from session 1
├── .env                                ← YOU CREATE THIS (step 3 below)
│
├── config/
│   ├── __init__.py
│   ├── asgi.py
│   ├── wsgi.py
│   ├── urls.py
│   └── settings/
│       ├── __init__.py
│       ├── base.py                     ← REPLACE with new version (session 2)
│       ├── development.py              ← already exists
│       ├── production.py               ← already exists
│       └── testing.py                  ← CREATE (session 1)
│
├── core/
│   ├── database/
│   │   ├── __init__.py                 ← CREATE (empty)
│   │   ├── base_model.py               ← CREATE (session 2)
│   │   ├── managers.py                 ← CREATE (session 2)
│   │   └── mixins.py                   ← CREATE (session 2)
│   │
│   ├── exceptions/
│   │   ├── base.py                     ← CREATE (session 1)
│   │   └── handler.py                  ← CREATE (session 1)
│   │
│   ├── kafka/
│   │   ├── __init__.py                 ← CREATE (empty)
│   │   ├── base_event.py               ← CREATE (session 2)
│   │   ├── consumer.py                 ← CREATE (session 2)
│   │   ├── producer.py                 ← CREATE (session 2)
│   │   └── topics.py                   ← CREATE (session 2)
│   │
│   ├── middleware/
│   │   ├── __init__.py                 ← CREATE (empty)
│   │   ├── exception_handler.py        ← CREATE (session 2)
│   │   ├── metrics.py                  ← CREATE (session 2)
│   │   └── request_logging.py          ← CREATE (session 2)
│   │
│   ├── pagination/
│   │   ├── __init__.py                 ← CREATE (empty)
│   │   ├── connection.py               ← CREATE (session 2)
│   │   └── cursor.py                   ← CREATE (session 2)
│   │
│   ├── redis/
│   │   ├── __init__.py                 ← CREATE (empty)
│   │   ├── cache.py                    ← CREATE (session 2)
│   │   ├── client.py                   ← CREATE (session 2)
│   │   └── rate_limit.py               ← CREATE (session 2)
│   │
│   ├── security/
│   │   ├── __init__.py                 ← CREATE (empty)
│   │   ├── app_version.py              ← CREATE (session 2)
│   │   ├── authentication.py           ← CREATE (session 2)
│   │   ├── hashing.py                  ← CREATE (session 2)
│   │   └── jwt.py                      ← CREATE (session 2)
│   │
│   └── testing/                        ← CREATE this folder
│       ├── __init__.py                 ← CREATE
│       ├── base.py                     ← CREATE (session 1)
│       ├── factories.py                ← CREATE (session 1)
│       └── mixins.py                   ← CREATE (session 1)
│
├── core/
│   └── tests/                          ← CREATE this folder inside core/
│       ├── __init__.py                 ← CREATE (empty)
│       ├── test_base_model.py          ← CREATE (session 2)
│       ├── test_exception_handler.py   ← CREATE (session 2)
│       ├── test_hashing.py             ← CREATE (session 2)
│       ├── test_kafka_producer.py      ← CREATE (session 2)
│       ├── test_rate_limiter.py        ← CREATE (session 2)
│       └── test_redis_client.py        ← CREATE (session 2)
│
├── apps/
│   └── users/
│       ├── exceptions.py               ← CREATE (session 1)
│       ├── selectors.py                ← CREATE (session 1)
│       ├── services.py                 ← CREATE (session 1)
│       └── tests/
│           ├── __init__.py             ← CREATE (empty — REQUIRED)
│           ├── conftest.py             ← CREATE (session 1)
│           ├── factories.py            ← CREATE (session 1)
│           ├── test_models.py          ← CREATE (session 1)
│           ├── test_selectors.py       ← CREATE (session 1)
│           ├── test_services.py        ← CREATE (session 1)
│           └── test_views.py           ← CREATE (session 1)
│
└── tests/                              ← CREATE at project root level
    ├── __init__.py                     ← CREATE (empty)
    ├── conftest.py                     ← CREATE (session 1)
    └── integration/
        ├── __init__.py                 ← CREATE (empty)
        └── test_user_post_flow.py      ← CREATE (session 1)
```

---

## 2. PREREQUISITES — Install these first

### System requirements
- Python 3.12+
- PostgreSQL 16
- Redis 7
- Docker + Docker Compose (recommended)

### Check your Python version
```bash
python --version       # must be 3.12+
python3 --version
```

### Install uv (fast Python package manager — you already have uv.lock)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# OR if you use pip:
pip install uv
```

---

## 3. CREATE YOUR .env FILE

Create a file called `.env` in your `backend/` folder (same level as manage.py):

```bash
# backend/.env

SECRET_KEY=your-super-secret-key-change-this-in-production-min-50-chars

# PostgreSQL
POSTGRES_DB=qommunity_db
POSTGRES_USER=qommunity_user
POSTGRES_PASSWORD=qommunity_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0

# Kafka (set to false for now — M1 uses MockKafkaProducer)
KAFKA_ENABLED=false
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# App version (mobile enforcement)
APP_MIN_VERSION=1.0.0

# Django
ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_SETTINGS_MODULE=config.settings.development
```

---

## 4. INSTALL DEPENDENCIES

```bash
# From inside your backend/ folder:
cd backend

# Install all dependencies using uv
uv sync

# OR if using pip directly:
pip install -r requirements.txt
```

### Required packages (add to pyproject.toml dependencies):
```toml
[project]
dependencies = [
    "django>=5.0",
    "djangorestframework>=3.15",
    "djangorestframework-simplejwt>=5.3",
    "django-redis>=5.4",
    "django-cors-headers>=4.3",
    "psycopg2-binary>=2.9",
    "python-dotenv>=1.0",
    "celery[redis]>=5.3",
    "python-json-logger>=2.0",
    "fakeredis>=2.20",          # for tests
    "factory-boy>=3.3",         # for tests
    "pytest>=8.0",              # for tests
    "pytest-django>=4.8",       # for tests
    "coverage>=7.4",            # for tests
]
```

---

## 5. START SERVICES (Docker — easiest)

```bash
# From backend/ folder — start PostgreSQL and Redis
docker compose up -d postgres redis

# Verify they are running
docker compose ps
```

### OR start manually without Docker:
```bash
# Start PostgreSQL (macOS with Homebrew)
brew services start postgresql@16

# Start Redis (macOS with Homebrew)
brew services start redis

# Start PostgreSQL (Ubuntu/Debian)
sudo systemctl start postgresql
sudo systemctl start redis
```

---

## 6. RUN MIGRATIONS

```bash
cd backend

# Set Django settings
export DJANGO_SETTINGS_MODULE=config.settings.development

# Run migrations
python manage.py migrate

# Verify (you should see applied migrations)
python manage.py showmigrations
```

---

## 7. START THE DEVELOPMENT SERVER

```bash
cd backend

export DJANGO_SETTINGS_MODULE=config.settings.development

python manage.py runserver
# Server starts at: http://127.0.0.1:8000/
```

### Verify it's working:
```bash
curl http://127.0.0.1:8000/api/
# Should return JSON (not HTML error page)
```

---

## 8. RUNNING TESTS

### IMPORTANT: Tests use a separate settings file
```bash
export DJANGO_SETTINGS_MODULE=config.settings.testing
```

### Run all tests:
```bash
cd backend
pytest
```

### Run only fast unit tests (no DB needed):
```bash
pytest -m unit
```

### Run a specific test file:
```bash
pytest core/tests/test_base_model.py -v
pytest core/tests/test_redis_client.py -v
pytest core/tests/test_exception_handler.py -v
pytest core/tests/test_kafka_producer.py -v
pytest core/tests/test_rate_limiter.py -v
pytest core/tests/test_hashing.py -v
```

### Run tests for a specific app:
```bash
pytest apps/users/tests/ -v
```

### Run with coverage report:
```bash
pytest --cov --cov-report=term-missing
```

### Run and see detailed output on failures:
```bash
pytest -v --tb=long
```

### Using Makefile shortcuts:
```bash
make test              # all tests
make test-unit         # unit tests only
make test-coverage     # with coverage
make test-app APP=users  # one app
make test-file FILE=core/tests/test_redis_client.py
```

---

## 9. VERIFY EACH COMPONENT WORKS

### Test Redis connection:
```bash
python manage.py shell
>>> from core.redis.client import check_redis_connection
>>> check_redis_connection()
# Should print: Redis health check: OK
```

### Test Kafka producer (MockKafkaProducer in dev):
```bash
python manage.py shell
>>> from core.kafka.producer import get_producer
>>> from core.kafka.base_event import BaseEvent
>>> producer = get_producer()
>>> print(type(producer))
# <class 'core.kafka.producer.MockKafkaProducer'>
```

### Test exception handler:
```bash
python manage.py shell
>>> from core.exceptions.base import NotFoundError
>>> raise NotFoundError("test")
# Should show: NotFoundError: Resource not found.
```

---

## 10. COMMON ERRORS & FIXES

### "SECRET_KEY is not set"
→ You forgot to create `.env` file. See Step 3.

### "could not connect to server" (PostgreSQL)
→ PostgreSQL is not running.
```bash
docker compose up -d postgres
# OR
brew services start postgresql@16
```

### "Connection refused" (Redis)
→ Redis is not running.
```bash
docker compose up -d redis
# OR
brew services start redis
```

### "ModuleNotFoundError: No module named 'fakeredis'"
→ Install test dependencies:
```bash
uv add fakeredis factory-boy pytest pytest-django --dev
```

### "No module named 'core'"
→ You're running pytest from the wrong directory.
```bash
cd backend    # must be inside backend/ folder
pytest
```

### Tests fail with "Table doesn't exist"
→ The test DB needs to be created:
```bash
pytest --create-db    # first time only
pytest --reuse-db     # subsequent runs (faster)
```

### "django.core.exceptions.ImproperlyConfigured: AUTH_USER_MODEL refers to model 'users.User' that has not been installed"
→ You haven't created the custom User model yet (that's M2 — next milestone).
→ For now, comment out `AUTH_USER_MODEL = "users.User"` in base.py and it will use Django's default User.

---

## 11. WHAT WORKS RIGHT NOW (M1 Complete)

| Component | Status | How to verify |
|---|---|---|
| BaseModel (UUID, timestamps, soft-delete) | ✅ | `pytest core/tests/test_base_model.py` |
| Exception handler (JSON envelope) | ✅ | `pytest core/tests/test_exception_handler.py` |
| Redis client + cache helpers | ✅ | `pytest core/tests/test_redis_client.py` |
| Rate limiter (token bucket) | ✅ | `pytest core/tests/test_rate_limiter.py` |
| Kafka producer (MockKafkaProducer) | ✅ | `pytest core/tests/test_kafka_producer.py` |
| Security hashing utils | ✅ | `pytest core/tests/test_hashing.py` |
| Middleware stack (logging, metrics) | ✅ | Start server + make a request |
| Cursor pagination | ✅ | Used in views (M2+) |
| Settings split (base/dev/test/prod) | ✅ | `python manage.py check` |

---

## QUICK START (everything in one go)

```bash
# 1. Enter project
cd backend

# 2. Create .env (copy from step 3 above)

# 3. Install dependencies
uv sync

# 4. Start services
docker compose up -d postgres redis

# 5. Run migrations
python manage.py migrate

# 6. Run all M1 tests
pytest core/tests/ -v

# 7. Start server
python manage.py runserver
```