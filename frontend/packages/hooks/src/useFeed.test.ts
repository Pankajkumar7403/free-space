import { describe, expect, it } from 'vitest';
import type { InfiniteData } from '@tanstack/react-query';
import type { FeedPage } from '@qommunity/types';
import { flattenFeedPages } from './useFeed';

describe('flattenFeedPages', () => {
  it('returns a flat post array across all pages', () => {
    const data: InfiniteData<FeedPage> = {
      pages: [
        {
          results: [
            {
              id: 'p1',
              author: {} as never,
              content: 'first',
              media: [],
              hashtags: [],
              visibility: 'public',
              is_anonymous: false,
              allow_comments: true,
              location: null,
              likes_count: 0,
              comments_count: 0,
              is_liked: false,
              is_bookmarked: false,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
              edited_at: null,
            },
          ],
          next_cursor: 2,
          source: 'db',
        },
        {
          results: [
            {
              id: 'p2',
              author: {} as never,
              content: 'second',
              media: [],
              hashtags: [],
              visibility: 'public',
              is_anonymous: false,
              allow_comments: true,
              location: null,
              likes_count: 0,
              comments_count: 0,
              is_liked: false,
              is_bookmarked: false,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
              edited_at: null,
            },
          ],
          next_cursor: null,
          source: 'db',
        },
      ],
      pageParams: [undefined, '2'],
    };

    const flattened = flattenFeedPages(data);
    expect(flattened).toHaveLength(2);
    expect(flattened[0]?.id).toBe('p1');
    expect(flattened[1]?.id).toBe('p2');
  });
});
