// 📍 LOCATION: free-space/frontend/packages/api-client/src/endpoints/feed.ts
//
// Feed API calls
// Base URL: /api/v1/feed/

import type { FeedPage } from '@qommunity/types';
import { apiClient } from '../instance';

export const feedApi = {
  /**
   * GET /api/v1/feed/
   * Returns cursor-paginated home feed from Redis ZSet + DB fallback.
   */
  getHomeFeed: async (cursor?: string): Promise<FeedPage> => {
    const { data } = await apiClient.get<FeedPage>('/feed/', { params: { cursor } });
    return data;
  },

  /**
   * GET /api/v1/feed/explore/
   * Trending posts by engagement score.
   */
  getExploreFeed: async (cursor?: string): Promise<FeedPage> => {
    const { data } = await apiClient.get<FeedPage>('/feed/explore/', { params: { cursor } });
    return data;
  },

  /**
   * GET /api/v1/feed/hashtag/{tag}/
   */
  getHashtagFeed: async (tag: string, cursor?: string): Promise<FeedPage> => {
    const { data } = await apiClient.get<FeedPage>(`/feed/hashtag/${tag}/`, {
      params: { cursor },
    });
    return data;
  },
};
