# ── Test commands ──────────────────────────────────────────────────────────────

.PHONY: test test-unit test-integration test-e2e test-coverage test-watch

## Run all tests
test:
	pytest

## Run only fast unit tests (no e2e, no integration)
test-unit:
	pytest -m "unit" --no-header -q

## Run integration tests only
test-integration:
	pytest -m "integration" --no-header -q

## Run e2e API tests only
test-e2e:
	pytest -m "e2e" --no-header -q

## Run a specific app's tests
test-app:
	pytest apps/$(APP)/tests/ -v

## Run with coverage report
test-coverage:
	pytest --cov --cov-report=term-missing --cov-report=html

## Run tests and open HTML coverage in browser
test-coverage-open: test-coverage
	open htmlcov/index.html

## Run tests for a single file (FILE=apps/users/tests/test_services.py)
test-file:
	pytest $(FILE) -v

## Watch mode (requires pytest-watch)
test-watch:
	ptw -- --testpaths apps tests -q

# ── Code quality ───────────────────────────────────────────────────────────────

.PHONY: lint format

lint:
	ruff check .

format:
	ruff format .

# ── Django management ──────────────────────────────────────────────────────────

.PHONY: migrate makemigrations shell

migrate:
	python manage.py migrate

makemigrations:
	python manage.py makemigrations

shell:
	python manage.py shell_plus