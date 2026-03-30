// 📍 LOCATION: free-space/frontend/apps/web/src/test/handlers/authHandlers.ts
//
// MSW handlers for auth endpoints.
// These are the DEFAULT handlers — used in all tests unless overridden.

import { http, HttpResponse } from 'msw';
import { mockUser, mockTokens } from '../factories';

const API = 'http://localhost:8000/api/v1';

export const authHandlers = [
  // POST /users/auth/login/
  http.post(`${API}/users/auth/login/`, async ({ request }) => {
    const body = (await request.json()) as { email: string; password: string };

    // Simulate wrong credentials
    if (body.password === 'wrong') {
      return HttpResponse.json(
        { error_code: 'AUTHENTICATION_FAILED', message: 'Invalid email or password.', details: {} },
        { status: 401 },
      );
    }

    return HttpResponse.json({ user: mockUser(), tokens: mockTokens() }, { status: 200 });
  }),

  // POST /users/auth/register/
  http.post(`${API}/users/auth/register/`, async ({ request }) => {
    const body = (await request.json()) as { username: string };

    // Simulate duplicate username
    if (body.username === 'taken') {
      return HttpResponse.json(
        {
          error_code: 'VALIDATION_ERROR',
          message: 'Validation failed.',
          details: { username: ['A user with this username already exists.'] },
        },
        { status: 400 },
      );
    }

    return HttpResponse.json(
      { user: mockUser({ username: body.username }), tokens: mockTokens(), email_verification_sent: true },
      { status: 201 },
    );
  }),

  // POST /users/auth/logout/
  http.post(`${API}/users/auth/logout/`, () =>
    HttpResponse.json({ ok: true }, { status: 200 }),
  ),

  // POST /users/auth/token/refresh/
  http.post(`${API}/users/auth/token/refresh/`, () =>
    HttpResponse.json({ access: mockTokens().access }, { status: 200 }),
  ),
];
