# Backend Development Guidelines

Project: Social Platform Backend\
Stack: Django + Django REST Framework\
Architecture: Modular Monolith\
Team Size: 2 Developers

------------------------------------------------------------------------

## 1. Project Structure

backend/ │ ├── apps/ │ ├── comments/ │ ├── common/ │ ├── feed/ │ ├──
likes/ │ ├── media/ │ ├── notifications/ │ ├── posts/ │ ├── users/ │ ├──
config/ ├── core/ ├── scripts/ ├── tests/ │ ├── manage.py ├──
pyproject.toml ├── docker-compose.yml

Rules: - Each feature module must live inside `apps/` - No business
logic inside `config/` - Shared utilities go inside `apps/common/` - No
cross-app circular imports

------------------------------------------------------------------------

## 2. Naming Conventions

### Python Files

-   snake_case.py
-   Example: serializers.py, views.py, services.py

### Classes

-   PascalCase
-   Example: UserViewSet, PostCreateSerializer

### Variables

-   snake_case
-   Example: user_id, created_at

### Constants

-   UPPER_SNAKE_CASE
-   Example: MAX_POST_CAPTION_LENGTH = 500

### Models

-   Singular, PascalCase
-   Example: User, Post, Comment

------------------------------------------------------------------------

## 3. App Internal Structure

Each app must contain:

models.py\
serializers.py\
views.py\
urls.py\
services.py\
selectors.py\
permissions.py\
tests/

Responsibilities: - models.py → DB schema - serializers.py →
validation + transformation - views.py → HTTP layer only - services.py →
business logic - selectors.py → read queries - permissions.py → access
control

Business logic inside views is forbidden.

------------------------------------------------------------------------

## 4. API Standards

Base Prefix: /api/v1/

Use plural nouns. No verbs in URLs.

Correct: POST /api/v1/posts/ GET /api/v1/posts/12/

Incorrect: /createPost /getUserList

------------------------------------------------------------------------

## 5. Standard Response Format

Success:

{ "success": true, "data": { ... }, "error": null }

Failure:

{ "success": false, "data": null, "error": { "code": "VALIDATION_ERROR",
"message": "Caption is required", "fields": { "caption": \["This field
is required."\] } } }

------------------------------------------------------------------------

## 6. Global Error Codes

VALIDATION_ERROR\
AUTHENTICATION_FAILED\
PERMISSION_DENIED\
NOT_FOUND\
RATE_LIMITED\
INTERNAL_SERVER_ERROR

All custom errors must be defined inside apps/common/exceptions.py

------------------------------------------------------------------------

## 7. Authentication Standard

JWT (Access + Refresh)

Endpoints: POST /api/v1/auth/register/\
POST /api/v1/auth/login/\
POST /api/v1/auth/refresh/\
POST /api/v1/auth/logout/

Login Response:

{ "success": true, "data": { "access_token": "...", "refresh_token":
"...", "user": { "id": "uuid", "username": "pankaj" } }, "error": null }

------------------------------------------------------------------------

## 8. Branching Strategy

main → production\
develop → integration\
feature/`<feature-name>`{=html}

Rules: - Never push directly to main - Every feature requires PR -
Mandatory review - No self-merge

------------------------------------------------------------------------

## 9. Definition of Done

A feature is complete only if: - API contract written - Tests
implemented - Error cases handled - Permissions implemented - Code
reviewed
