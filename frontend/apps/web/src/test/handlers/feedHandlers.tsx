// 📍 LOCATION: free-space/frontend/apps/web/src/test/handlers/feedHandlers.ts

import { http, HttpResponse } from 'msw';
import { mockPost, mockUserSummary } from '../factories';
import type { FeedPage } from '@qommunity/types';

const API = 'http://localhost:8000/api/v1';

function makeFeedPage(cursor?: string): FeedPage {
  const posts = Array.from({ length: 5 }, () => ({
    id:        `feed-item-${Math.random().toString(36).slice(2, 9)}`,
    post:      mockPost(),
    score:     Math.random() * 100,
    source:    'follow' as const,
    timestamp: new Date().toISOString(),
  }));

  return {
    results:  posts,
    next:     cursor === 'page2' ? null : 'page2',
    previous: null,
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