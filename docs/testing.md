# Testing Guide

## Stack
- **pytest** + **pytest-django** — test runner
- **factory-boy** — model factories (no raw `User.objects.create` in tests)
- **coverage.py** — branch-level coverage with 80% minimum gate

---

## How to Run Tests

```bash
# All tests
make test

# Fast unit tests only (good for TDD inner loop)
make test-unit

# Integration tests
make test-integration

# E2E API tests
make test-e2e

# Single app
make test-app APP=users

# Single file
make test-file FILE=apps/users/tests/test_services.py

# With coverage
make test-coverage
```

---

## Test Layers & Markers

| Marker        | What it tests                      | Uses DB? | Uses HTTP? | Speed  |
|---------------|------------------------------------|----------|------------|--------|
| `unit`        | selectors, services, models        | ✅        | ❌          | Fast   |
| `integration` | cross-app flows, Celery tasks      | ✅        | Partial    | Medium |
| `e2e`         | full API request → response        | ✅        | ✅          | Slow   |
| `slow`        | anything > 1 second                | varies   | varies     | Slow   |

---

## Directory Layout

```
backend/
├── apps/
│   └── users/
│       └── tests/
│           ├── __init__.py       ← required for pytest discovery
│           ├── conftest.py       ← app-specific fixtures
│           ├── factories.py      ← UserFactory, etc.
│           ├── test_models.py    ← model constraints/properties  [unit]
│           ├── test_selectors.py ← read query tests              [unit]
│           ├── test_services.py  ← write logic tests             [unit]
│           └── test_views.py     ← API endpoint tests            [e2e]
│
├── core/
│   └── testing/
│       ├── base.py       ← BaseTestCase, BaseAPITestCase + assert helpers
│       ├── factories.py  ← BaseFactory (all app factories inherit this)
│       └── mixins.py     ← CacheMixin, KafkaMockMixin, etc.
│
└── tests/
    ├── conftest.py                        ← project-wide fixtures
    └── integration/
        └── test_user_post_flow.py         ← cross-app smoke tests
```

---

## Adding Tests for a New App

1. Add `__init__.py` to the `tests/` folder (required!).
2. Copy `apps/users/tests/conftest.py` → `apps/<yourapp>/tests/conftest.py`.
3. Create `factories.py` inheriting from `core.testing.factories.BaseFactory`.
4. Write `test_models.py`, `test_selectors.py`, `test_services.py`, `test_views.py`.
5. Use `from core.testing.base import BaseAPITestCase` for view tests.
6. Run `make test-app APP=<yourapp>` to verify.

---

## Coverage Gate

Coverage must stay **≥ 80%** (enforced by `fail_under = 80` in `pyproject.toml`).  
Migrations, `__init__.py`, and test files are excluded from measurement.