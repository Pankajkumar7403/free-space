// 📍 LOCATION: free-space/frontend/apps/web/src/test/handlers/authHandlers.ts
//
// MSW handlers for auth endpoints.
// Paths match api-client: /api/v1/users/login/ (no /auth/ segment).

import { http, HttpResponse } from 'msw';
import { mockUser, mockTokens } from '../factories';

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8000/api/v1';

export const authHandlers = [
  http.post('/api/auth/set-cookie', () =>
    HttpResponse.json({ ok: true }, { status: 200 }),
  ),
  http.post('/api/auth/logout', () =>
    HttpResponse.json({ ok: true }, { status: 200 }),
  ),
  http.get('/api/auth/session', () =>
    HttpResponse.json({ error: 'no session' }, { status: 401 }),
  ),

  http.post(`${API}/users/login/`, async ({ request }) => {
    const body = (await request.json()) as { email: string; password: string };

    if (body.password === 'wrong') {
      return HttpResponse.json(
        { error: { code: 'AUTHENTICATION_FAILED', message: 'Invalid email or password.', detail: {} } },
        { status: 401 },
      );
    }

    return HttpResponse.json({ user: mockUser(), tokens: mockTokens() }, { status: 200 });
  }),

  http.post(`${API}/users/register/`, async ({ request }) => {
    const body = (await request.json()) as { username: string };

    if (body.username === 'taken') {
      return HttpResponse.json(
        {
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Validation failed.',
            detail: { username: ['A user with this username already exists.'] },
          },
        },
        { status: 400 },
      );
    }

    return HttpResponse.json(
      {
        user: mockUser({ username: body.username }),
        tokens: mockTokens(),
        email_verification_sent: true,
      },
      { status: 201 },
    );
  }),

  http.post(`${API}/users/logout/`, () =>
    HttpResponse.json({ ok: true }, { status: 200 }),
  ),

  http.post(`${API}/users/token/refresh/`, () =>
    HttpResponse.json({ access: mockTokens().access }, { status: 200 }),
  ),
];
