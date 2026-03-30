// 📍 LOCATION: free-space/frontend/apps/web/src/test/handlers/userHandlers.ts

import { http, HttpResponse } from 'msw';
import { mockUser, mockUserSummary } from '../factories';
import type { PaginatedResponse } from '@qommunity/types';

const API = 'http://localhost:8000/api/v1';

export const userHandlers = [
  http.get(`${API}/users/me/`, () =>
    HttpResponse.json(mockUser(), { status: 200 }),
  ),

  http.get(`${API}/users/search/`, ({ request }) => {
    const url = new URL(request.url);
    const q   = url.searchParams.get('q') ?? '';
    const results = q.length > 0
      ? [mockUserSummary({ username: `result_${q}`, display_name: `Result for ${q}` })]
      : [];
    return HttpResponse.json(
      { results, next: null, previous: null, count: results.length } satisfies PaginatedResponse<ReturnType<typeof mockUserSummary>>,
      { status: 200 },
    );
  }),

  http.get(`${API}/users/:username/followers/`, () =>
    HttpResponse.json(
      { results: [mockUserSummary(), mockUserSummary()], next: null, previous: null, count: 2 },
      { status: 200 },
    ),
  ),

  http.get(`${API}/users/:username/following/`, () =>
    HttpResponse.json(
      { results: [mockUserSummary()], next: null, previous: null, count: 1 },
      { status: 200 },
    ),
  ),

  // This must come AFTER the more-specific routes above
  http.get(`${API}/users/:username/`, ({ params }) =>
    HttpResponse.json(
      mockUser({ username: params['username'] as string }),
      { status: 200 },
    ),
  ),

  http.post(`${API}/users/:username/follow/`, () =>
    HttpResponse.json({ status: 'following' }, { status: 201 }),
  ),

  http.delete(`${API}/users/:username/follow/`, () =>
    new HttpResponse(null, { status: 204 }),
  ),

  http.post(`${API}/users/:username/block/`, () =>
    new HttpResponse(null, { status: 204 }),
  ),

  http.delete(`${API}/users/:username/block/`, () =>
    new HttpResponse(null, { status: 204 }),
  ),

  http.post(`${API}/users/:username/mute/`, () =>
    new HttpResponse(null, { status: 204 }),
  ),

  http.delete(`${API}/users/:username/mute/`, () =>
    new HttpResponse(null, { status: 204 }),
  ),
];