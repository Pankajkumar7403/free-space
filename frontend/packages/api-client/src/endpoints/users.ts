// 📍 LOCATION: free-space/frontend/packages/api-client/src/endpoints/users.ts
//
// User & social graph API calls
// Base URL: /api/v1/users/

import type {
    User,
    AuthenticatedUser,
    UserSummary,
    PaginatedResponse,
  } from '@qommunity/types';
  
  import { apiClient } from '../instance';
  
  const BASE = '/users';
  
  export const usersApi = {
    /**
     * GET /api/v1/users/me/
     * Returns the authenticated user's full profile.
     */
    getMe: async (): Promise<AuthenticatedUser> => {
      const { data } = await apiClient.get<AuthenticatedUser>(`${BASE}/me/`);
      return data;
    },
  
    /**
     * PATCH /api/v1/users/me/
     * Partial update of authenticated user's profile.
     */
    updateMe: async (payload: Partial<AuthenticatedUser>): Promise<AuthenticatedUser> => {
      const { data } = await apiClient.patch<AuthenticatedUser>(`${BASE}/me/`, payload);
      return data;
    },
  
    /**
     * GET /api/v1/users/{username}/
     * Fetch another user's public profile.
     * Respects account_privacy — returns 404 for private accounts if not following.
     */
    getProfile: async (username: string): Promise<User> => {
      const { data } = await apiClient.get<User>(`${BASE}/${username}/`);
      return data;
    },
  
    /**
     * GET /api/v1/users/search/?q={query}
     * Full-text search on username + display_name.
     * Returns slim UserSummary list.
     */
    searchUsers: async (
      query: string,
      cursor?: string,
    ): Promise<PaginatedResponse<UserSummary>> => {
      const { data } = await apiClient.get<PaginatedResponse<UserSummary>>(`${BASE}/search/`, {
        params: { q: query, cursor },
      });
      return data;
    },
  
    // ─── Social graph ───────────────────────────────────────────────────────────
  
    /**
     * POST /api/v1/users/{username}/follow/
     * Follow a user. Returns 201 for direct follow, 202 for follow request (private account).
     */
    followUser: async (username: string): Promise<{ status: 'following' | 'requested' }> => {
      const { data } = await apiClient.post<{ status: 'following' | 'requested' }>(
        `${BASE}/${username}/follow/`,
      );
      return data;
    },
  
    /**
     * DELETE /api/v1/users/{username}/follow/
     * Unfollow or cancel follow request.
     */
    unfollowUser: async (username: string): Promise<void> => {
      await apiClient.delete(`${BASE}/${username}/follow/`);
    },
  
    /**
     * GET /api/v1/users/{username}/followers/
     */
    getFollowers: async (
      username: string,
      cursor?: string,
    ): Promise<PaginatedResponse<UserSummary>> => {
      const { data } = await apiClient.get<PaginatedResponse<UserSummary>>(
        `${BASE}/${username}/followers/`,
        { params: { cursor } },
      );
      return data;
    },
  
    /**
     * GET /api/v1/users/{username}/following/
     */
    getFollowing: async (
      username: string,
      cursor?: string,
    ): Promise<PaginatedResponse<UserSummary>> => {
      const { data } = await apiClient.get<PaginatedResponse<UserSummary>>(
        `${BASE}/${username}/following/`,
        { params: { cursor } },
      );
      return data;
    },
  
    /**
     * POST /api/v1/users/{username}/block/
     */
    blockUser: async (username: string): Promise<void> => {
      await apiClient.post(`${BASE}/${username}/block/`);
    },
  
    /**
     * DELETE /api/v1/users/{username}/block/
     */
    unblockUser: async (username: string): Promise<void> => {
      await apiClient.delete(`${BASE}/${username}/block/`);
    },
  
    /**
     * POST /api/v1/users/{username}/mute/
     */
    muteUser: async (username: string): Promise<void> => {
      await apiClient.post(`${BASE}/${username}/mute/`);
    },
  
    /**
     * DELETE /api/v1/users/{username}/mute/
     */
    unmuteUser: async (username: string): Promise<void> => {
      await apiClient.delete(`${BASE}/${username}/mute/`);
    },
  };
  