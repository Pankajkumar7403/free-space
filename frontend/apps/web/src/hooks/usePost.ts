// 📍 LOCATION: free-space/frontend/packages/hooks/src/usePost.ts

import {
    useQuery,
    useMutation,
    useInfiniteQuery,
    useQueryClient,
    type InfiniteData,
  } from '@tanstack/react-query';
  import { postsApi } from '@qommunity/api-client';
  import type { FeedPage, Post, PaginatedResponse } from '@qommunity/types';
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
        void queryClient.invalidateQueries({ queryKey: queryKeys.feed.all() });
      },
    });
  }

  // ─── Bookmark toggle (optimistic, all feed caches) ───────────────────────────
  export function useBookmarkPost() {
    const queryClient = useQueryClient();

    return useMutation({
      mutationFn: ({
        postId,
        isBookmarked,
      }: {
        postId: string;
        isBookmarked: boolean;
      }) =>
        isBookmarked
          ? postsApi.removeBookmark(postId)
          : postsApi.bookmarkPost(postId),

      onMutate: async ({ postId, isBookmarked }) => {
        await queryClient.cancelQueries({ queryKey: queryKeys.feed.all() });
        const previousQueries = queryClient.getQueriesData<InfiniteData<FeedPage>>({
          queryKey: queryKeys.feed.all(),
        });

        queryClient.setQueriesData<InfiniteData<FeedPage>>(
          { queryKey: queryKeys.feed.all() },
          (old) => {
            if (!old) return old;
            return {
              ...old,
              pages: old.pages.map((page) => ({
                ...page,
                results: page.results.map((post) => {
                  if (post.id !== postId) return post;
                  return { ...post, is_bookmarked: !isBookmarked };
                }),
              })),
            };
          },
        );

        return { previousQueries };
      },

      onError: (_err, _vars, context) => {
        context?.previousQueries?.forEach(([queryKey, data]) => {
          queryClient.setQueryData(queryKey, data);
        });
      },

      onSettled: () => {
        void queryClient.invalidateQueries({ queryKey: queryKeys.feed.all() });
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