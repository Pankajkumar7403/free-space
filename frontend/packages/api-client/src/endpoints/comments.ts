// 📍 LOCATION: free-space/frontend/packages/api-client/src/endpoints/comments.ts
//
// Comments API calls
// Base URL: /api/v1/comments/

import type {
    Comment,
    CreateCommentPayload,
    UpdateCommentPayload,
    PaginatedResponse,
  } from '@qommunity/types';
  
  import { apiClient } from '../instance';
  
  const BASE = '/comments';
  
  export const commentsApi = {
    /**
     * GET /api/v1/comments/?post_id={postId}
     * Top-level comments only (parent_id = null), cursor-paginated.
     */
    getPostComments: async (
      postId: string,
      cursor?: string,
    ): Promise<PaginatedResponse<Comment>> => {
      const { data } = await apiClient.get<PaginatedResponse<Comment>>(`${BASE}/`, {
        params: { post_id: postId, cursor },
      });
      return data;
    },
  
    /**
     * GET /api/v1/comments/{commentId}/replies/
     * Lazy-loaded replies for a comment thread.
     */
    getReplies: async (
      commentId: string,
      cursor?: string,
    ): Promise<PaginatedResponse<Comment>> => {
      const { data } = await apiClient.get<PaginatedResponse<Comment>>(
        `${BASE}/${commentId}/replies/`,
        { params: { cursor } },
      );
      return data;
    },
  
    /**
     * POST /api/v1/comments/
     */
    createComment: async (payload: CreateCommentPayload): Promise<Comment> => {
      const { data } = await apiClient.post<Comment>(`${BASE}/`, payload);
      return data;
    },
  
    /**
     * PATCH /api/v1/comments/{commentId}/
     */
    updateComment: async (commentId: string, payload: UpdateCommentPayload): Promise<Comment> => {
      const { data } = await apiClient.patch<Comment>(`${BASE}/${commentId}/`, payload);
      return data;
    },
  
    /**
     * DELETE /api/v1/comments/{commentId}/
     * Soft delete — shows "deleted comment" placeholder in thread.
     */
    deleteComment: async (commentId: string): Promise<void> => {
      await apiClient.delete(`${BASE}/${commentId}/`);
    },
  
    /**
     * POST /api/v1/comments/{commentId}/like/
     */
    likeComment: async (
      commentId: string,
    ): Promise<{ is_liked: boolean; likes_count: number }> => {
      const { data } = await apiClient.post<{ is_liked: boolean; likes_count: number }>(
        `${BASE}/${commentId}/like/`,
      );
      return data;
    },
  
    /**
     * POST /api/v1/comments/{commentId}/pin/
     * Only post author can pin.
     */
    pinComment: async (commentId: string): Promise<void> => {
      await apiClient.post(`${BASE}/${commentId}/pin/`);
    },
  
    /**
     * POST /api/v1/comments/{commentId}/hide/
     * Post author or comment author can hide.
     */
    hideComment: async (commentId: string): Promise<void> => {
      await apiClient.post(`${BASE}/${commentId}/hide/`);
    },
  
    /**
     * POST /api/v1/comments/{commentId}/report/
     */
    reportComment: async (commentId: string, reason: string): Promise<void> => {
      await apiClient.post(`${BASE}/${commentId}/report/`, { reason });
    },
  };
  