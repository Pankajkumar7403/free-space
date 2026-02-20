# API Contract Documentation

Base URL: /api/v1/

All endpoints must follow the standard response format.

------------------------------------------------------------------------

## 1. Authentication APIs

### Register

POST /api/v1/auth/register/

Request:

{ "username": "string", "email": "string", "password": "string" }

Response (201):

{ "success": true, "data": { "id": "uuid", "username": "string",
"email": "string" }, "error": null }

------------------------------------------------------------------------

### Login

POST /api/v1/auth/login/

Request:

{ "email": "string", "password": "string" }

Response (200):

{ "success": true, "data": { "access_token": "string", "refresh_token":
"string", "user": { "id": "uuid", "username": "string" } }, "error":
null }

------------------------------------------------------------------------

## 2. Posts APIs

### Create Post

POST /api/v1/posts/

Request:

{ "caption": "string", "media_url": "string" }

Response (201):

{ "success": true, "data": { "id": "uuid", "caption": "string",
"media_url": "string", "author": { "id": "uuid", "username": "string" },
"created_at": "datetime" }, "error": null }

------------------------------------------------------------------------

### Get Post

GET /api/v1/posts/{id}/

Response (200):

{ "success": true, "data": { "id": "uuid", "caption": "string",
"media_url": "string", "author": { "id": "uuid", "username": "string" },
"created_at": "datetime" }, "error": null }

------------------------------------------------------------------------

## 3. Error Format

All failures must follow:

{ "success": false, "data": null, "error": { "code": "ERROR_CODE",
"message": "Human readable message", "fields": {} } }
