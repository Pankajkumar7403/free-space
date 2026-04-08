// 📍 LOCATION: free-space/frontend/packages/api-client/src/endpoints/posts.ts
//
// Posts API calls
// Base URL: /api/v1/posts/

import type {
    Post,
    CreatePostPayload,
    UpdatePostPayload,
    PresignedUploadUrl,
    PaginatedResponse,
    MediaType,
  } from '@qommunity/types';
  
  import { apiClient } from '../instance';
  
  const BASE = '/posts';
  
  export const postsApi = {
    /**
     * POST /api/v1/posts/
     * Create a new post. media_ids must reference already-uploaded media records.
     */
    createPost: async (payload: CreatePostPayload): Promise<Post> => {
      const { data } = await apiClient.post<Post>(`${BASE}/`, payload);
      return data;
    },
  
    /**
     * GET /api/v1/posts/{postId}/
     */
    getPost: async (postId: string): Promise<Post> => {
      const { data } = await apiClient.get<Post>(`${BASE}/${postId}/`);
      return data;
    },
  
    /**
     * PATCH /api/v1/posts/{postId}/
     */
    updatePost: async (postId: string, payload: UpdatePostPayload): Promise<Post> => {
      const { data } = await apiClient.patch<Post>(`${BASE}/${postId}/`, payload);
      return data;
    },
  
    /**
     * DELETE /api/v1/posts/{postId}/
     * Soft delete — returns 204, post becomes 404 to other consumers.
     */
    deletePost: async (postId: string): Promise<void> => {
      await apiClient.delete(`${BASE}/${postId}/`);
    },
  
    /**
     * GET /api/v1/posts/?username={username}
     * Get posts for a user's profile grid.
     */
    getUserPosts: async (
      username: string,
      cursor?: string,
    ): Promise<PaginatedResponse<Post>> => {
      const { data } = await apiClient.get<PaginatedResponse<Post>>(`${BASE}/`, {
        params: { username, cursor },
      });
      return data;
    },
  
    // ─── Likes ──────────────────────────────────────────────────────────────────
  
    /**
     * POST /api/v1/posts/{postId}/like/
     * Toggle like. Returns new like state + count.
     */
    likePost: async (postId: string): Promise<{ is_liked: boolean; likes_count: number }> => {
      const { data } = await apiClient.post<{ is_liked: boolean; likes_count: number }>(
        `${BASE}/${postId}/like/`,
      );
      return data;
    },
  
    /**
     * DELETE /api/v1/posts/{postId}/like/
     */
    unlikePost: async (postId: string): Promise<{ is_liked: boolean; likes_count: number }> => {
      const { data } = await apiClient.delete<{ is_liked: boolean; likes_count: number }>(
        `${BASE}/${postId}/like/`,
      );
      return data;
    },
  
    // ─── Bookmarks ───────────────────────────────────────────────────────────────
  
    /**
     * POST /api/v1/posts/{postId}/bookmark/
     */
    bookmarkPost: async (postId: string): Promise<void> => {
      await apiClient.post(`${BASE}/${postId}/bookmark/`);
    },
  
    /**
     * DELETE /api/v1/posts/{postId}/bookmark/
     */
    removeBookmark: async (postId: string): Promise<void> => {
      await apiClient.delete(`${BASE}/${postId}/bookmark/`);
    },
  
    // ─── Media upload ────────────────────────────────────────────────────────────
  
    /**
     * POST /api/v1/posts/media/presign/
     * Step 1 of the S3 upload flow. Backend creates a media record and returns
     * a presigned URL. Client uploads directly to S3, then calls confirmUpload.
     */
    getPresignedUploadUrl: async (payload: {
      file_type: MediaType;
      file_size: number;
      mime_type: string;
    }): Promise<PresignedUploadUrl> => {
      const { data } = await apiClient.post<PresignedUploadUrl>(
        '/posts/media/presign/',
        payload,
      );
      return data;
    },
  
    /**
     * POST /api/v1/posts/media/{mediaId}/confirm/
     * Step 3: After S3 upload completes, tell backend to start Celery transcoding.
     */
    confirmUpload: async (mediaId: string): Promise<void> => {
      await apiClient.post(`/posts/media/${mediaId}/confirm/`);
    },
  };
  