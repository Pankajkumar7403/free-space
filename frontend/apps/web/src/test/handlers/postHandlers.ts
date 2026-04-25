// 📍 LOCATION: free-space/frontend/apps/web/src/test/handlers/postHandlers.ts
//
// MSW handlers for post actions used across component tests.

import { http, HttpResponse } from 'msw';

const API = 'http://localhost:8000/api/v1';

export const postHandlers = [
  http.post(`${API}/posts/:postId/like/`, () =>
    HttpResponse.json({ is_liked: true, likes_count: 6 }, { status: 200 }),
  ),

  http.delete(`${API}/posts/:postId/like/`, () =>
    HttpResponse.json({ is_liked: false, likes_count: 4 }, { status: 200 }),
  ),

  http.post(`${API}/posts/:postId/bookmark/`, () => new HttpResponse(null, { status: 204 })),

  http.delete(`${API}/posts/:postId/bookmark/`, () => new HttpResponse(null, { status: 204 })),
];
