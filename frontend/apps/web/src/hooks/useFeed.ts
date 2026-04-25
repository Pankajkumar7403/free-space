// 📍 LOCATION: free-space/frontend/packages/hooks/src/useFeed.ts
//
// useFeed — TanStack Query hook for cursor-paginated feed data.
// Used by: web FeedList, mobile FeedScreen.
//
// Architecture:
//   useInfiniteQuery fetches pages using cursor-based pagination.
//   Each page returns { results, next_cursor, source } (backend contract).
//   The next_cursor value is passed as the `cursor` query param for the following page.
//   IntersectionObserver in InfiniteScrollList triggers fetchNextPage().

import {
    useInfiniteQuery,
    useMutation,
    useQueryClient,
    type InfiniteData,
  } from '@tanstack/react-query';
import { feedApi, postsApi } from '@qommunity/api-client';
import type { FeedPage, Post } from '@qommunity/types';
  import { queryKeys } from './queryKeys';
  
  // ─── Home feed ────────────────────────────────────────────────────────────────
  export function useHomeFeed() {
    return useInfiniteQuery<FeedPage, Error, InfiniteData<FeedPage>, ReturnType<typeof queryKeys.feed.home>, string | undefined>({
      queryKey: queryKeys.feed.home(),
      queryFn: ({ pageParam }) => feedApi.getHomeFeed(pageParam),
      initialPageParam: undefined,
      getNextPageParam: (lastPage) =>
        lastPage.next_cursor !== null ? String(lastPage.next_cursor) : undefined,
      staleTime: 30_000,  // Feed data fresh for 30s — matches backend Redis TTL
    });
  }
  
  // ─── Explore feed ─────────────────────────────────────────────────────────────
  export function useExploreFeed() {
    return useInfiniteQuery<FeedPage, Error, InfiniteData<FeedPage>, ReturnType<typeof queryKeys.feed.explore>, string | undefined>({
      queryKey: queryKeys.feed.explore(),
      queryFn: ({ pageParam }) => feedApi.getExploreFeed(pageParam),
      initialPageParam: undefined,
      getNextPageParam: (lastPage) =>
        lastPage.next_cursor !== null ? String(lastPage.next_cursor) : undefined,
      staleTime: 60_000,
    });
  }
  
  // ─── Hashtag feed ─────────────────────────────────────────────────────────────
  export function useHashtagFeed(tag: string) {
    return useInfiniteQuery<FeedPage, Error, InfiniteData<FeedPage>, ReturnType<typeof queryKeys.feed.hashtag>, string | undefined>({
      queryKey: queryKeys.feed.hashtag(tag),
      queryFn: ({ pageParam }) => feedApi.getHashtagFeed(tag, pageParam),
      initialPageParam: undefined,
      getNextPageParam: (lastPage) =>
        lastPage.next_cursor !== null ? String(lastPage.next_cursor) : undefined,
      enabled: tag.length > 0,
      staleTime: 60_000,
    });
  }
  
  // ─── Flatten pages → flat item array (used by components) ────────────────────
export function flattenFeedPages(data: InfiniteData<FeedPage> | undefined): Post[] {
    if (!data) return [];
    return data.pages.flatMap((page) => page.results);
  }
  
  // ─── Like mutation with optimistic update ────────────────────────────────────
  // Optimistic update: UI updates immediately, rolls back if API fails.
  // This is the Instagram pattern — never wait for the network to show a heart.
  export function useLikePost() {
    const queryClient = useQueryClient();
  
    return useMutation({
      mutationFn: ({ postId, isLiked }: { postId: string; isLiked: boolean }) =>
        isLiked ? postsApi.unlikePost(postId) : postsApi.likePost(postId),
  
      // onMutate fires BEFORE the API call — update every feed query (home, explore, hashtag)
      onMutate: async ({ postId, isLiked }) => {
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
                  return {
                    ...post,
                    is_liked: !isLiked,
                    likes_count: isLiked
                      ? Math.max(0, post.likes_count - 1)
                      : post.likes_count + 1,
                  };
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

      // Apply authoritative counts from the API — avoids immediate refetch of feed
      // (inactive feed queries + missing MSW handlers should not wipe optimistic UI).
      onSuccess: (data, { postId }) => {
        queryClient.setQueriesData<InfiniteData<FeedPage>>(
          { queryKey: queryKeys.feed.all() },
          (old) => {
            if (!old) return old;
            return {
              ...old,
              pages: old.pages.map((page) => ({
                ...page,
                results: page.results.map((post) =>
                  post.id === postId
                    ? {
                        ...post,
                        is_liked: data.is_liked,
                        likes_count: data.likes_count,
                      }
                    : post,
                ),
              })),
            };
          },
        );
      },
    });
  }