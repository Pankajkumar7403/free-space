// 📍 LOCATION: free-space/frontend/packages/types/src/feed.ts
//
// Feed types — mirror backend apps/feed/models.py

import type { Post } from './post';

export const FEED_SOURCE = ['follow', 'hashtag', 'explore', 'close_friends'] as const;
export type FeedSource = (typeof FEED_SOURCE)[number];

export interface FeedItem {
  id: string;
  post: Post;
  score: number;          // ranking score from Redis ZSet
  source: FeedSource;     // why this post is in this user's feed
  timestamp: string;      // ISO 8601 UTC — when added to feed
}

export interface FeedPage {
  results: FeedItem[];
  next: string | null;    // cursor for next page
  previous: string | null;
}
