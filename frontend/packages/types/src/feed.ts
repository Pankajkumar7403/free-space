// 📍 LOCATION: free-space/frontend/packages/types/src/feed.ts
//
// Feed types — mirror backend apps/feed/models.py

import type { Post } from './post';

export const FEED_SOURCE = ['follow', 'hashtag', 'explore', 'close_friends'] as const;
export type FeedSource = (typeof FEED_SOURCE)[number];

export interface FeedPage {
  // Backend currently serializes feed responses as a flat list of posts.
  results: Post[];
  next_cursor: number | null;
  source: string;
}
