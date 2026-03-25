// 📍 LOCATION: free-space/frontend/apps/web/src/test/handlers/userHandlers.ts

import { http, HttpResponse } from 'msw';
import { mockUser } from '../factories';

const API = 'http://localhost:8000/api/v1';

export const userHandlers = [
  // GET /users/me/
  http.get(`${API}/users/me/`, () =>
    HttpResponse.json(mockUser(), { status: 200 }),
  ),

  // GET /users/:username/
  http.get(`${API}/users/:username/`, ({ params }) =>
    HttpResponse.json(
      mockUser({ username: params.username as string }),
      { status: 200 },
    ),
  ),

  // POST /users/:username/follow/
  http.post(`${API}/users/:username/follow/`, () =>
    HttpResponse.json({ status: 'following' }, { status: 201 }),
  ),

  // DELETE /users/:username/follow/
  http.delete(`${API}/users/:username/follow/`, () =>
    new HttpResponse(null, { status: 204 }),
  ),
];
