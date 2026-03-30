// 📍 LOCATION: free-space/frontend/packages/hooks/src/usePost.ts

import {
    useQuery,
    useMutation,
    useInfiniteQuery,
    useQueryClient,
    type InfiniteData,
  } from '@tanstack/react-query';
  import { postsApi } from '@qommunity/api-client';
  import type { Post, PaginatedResponse } from '@qommunity/types';
  import { queryKeys } from './queryKeys';
  
  // ─── Single post detail ───────────────────────────────────────────────────────
  export function usePost(postId: string) {
    return useQuery({
      queryKey: queryKeys.posts.detail(postId),
      queryFn:  () => postsApi.getPost(postId),
      enabled:  postId.length > 0,
      staleTime: 60_000,
    });
  }
  
  // ─── User posts grid ──────────────────────────────────────────────────────────
  export function useUserPosts(username: string) {
    return useInfiniteQuery<
      PaginatedResponse<Post>,
      Error,
      InfiniteData<PaginatedResponse<Post>>,
      ReturnType<typeof queryKeys.posts.byUser>,
      string | undefined
    >({
      queryKey: queryKeys.posts.byUser(username),
      queryFn:  ({ pageParam }) => postsApi.getUserPosts(username, pageParam),
      initialPageParam: undefined,
      getNextPageParam: (lastPage) => lastPage.next ?? undefined,
      enabled: username.length > 0,
      staleTime: 30_000,
    });
  }
  
  // ─── Create post ──────────────────────────────────────────────────────────────
  export function useCreatePost() {
    const queryClient = useQueryClient();
  
    return useMutation({
      mutationFn: postsApi.createPost,
      onSuccess: () => {
        // Invalidate home feed and user posts — new post should appear
        void queryClient.invalidateQueries({ queryKey: queryKeys.feed.home() });
      },
    });
  }
  
  // ─── Delete post ──────────────────────────────────────────────────────────────
  export function useDeletePost() {
    const queryClient = useQueryClient();
  
    return useMutation({
      mutationFn: postsApi.deletePost,
      onSuccess: (_data, postId) => {
        // Remove from detail cache
        queryClient.removeQueries({ queryKey: queryKeys.posts.detail(postId) });
        // Invalidate feed — post should disappear
        void queryClient.invalidateQueries({ queryKey: queryKeys.feed.all() });
      },
    });
  }
  
  // ─── Flatten user post pages ──────────────────────────────────────────────────
  export function flattenPostPages(
    data: InfiniteData<PaginatedResponse<Post>> | undefined,
  ): Post[] {
    if (!data) return [];
    return data.pages.flatMap((page) => page.results);
  }