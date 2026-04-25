// 📍 LOCATION: free-space/frontend/apps/web/src/test/handlers/feedHandlers.ts

import { http, HttpResponse } from 'msw';
import { mockPost } from '../factories';
import type { FeedPage } from '@qommunity/types';

const API = 'http://localhost:8000/api/v1';

function makeFeedPage(cursor?: string): FeedPage {
  const posts = Array.from({ length: 5 }, () => mockPost());

  return {
    results: posts,
    next_cursor: cursor === '5' ? null : 5,
    source: 'db',
  };
}

export const feedHandlers = [
  // GET /feed/
  http.get(`${API}/feed/`, ({ request }) => {
    const url    = new URL(request.url);
    const cursor = url.searchParams.get('cursor') ?? undefined;
    return HttpResponse.json(makeFeedPage(cursor), { status: 200 });
  }),

  // GET /feed/explore/
  http.get(`${API}/feed/explore/`, () =>
    HttpResponse.json(makeFeedPage(), { status: 200 }),
  ),

  // POST /posts/:id/like/
  http.post(`${API}/posts/:postId/like/`, () =>
    HttpResponse.json({ is_liked: true, likes_count: 1 }, { status: 200 }),
  ),

  // DELETE /posts/:id/like/
  http.delete(`${API}/posts/:postId/like/`, () =>
    HttpResponse.json({ is_liked: false, likes_count: 0 }, { status: 200 }),
  ),
];