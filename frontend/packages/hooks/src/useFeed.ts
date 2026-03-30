// 📍 LOCATION: free-space/frontend/packages/hooks/src/useFeed.ts
//
// useFeed — TanStack Query hook for cursor-paginated feed data.
// Used by: web FeedList, mobile FeedScreen.
//
// Architecture:
//   useInfiniteQuery fetches pages using cursor-based pagination.
//   Each page returns { results, next, previous }.
//   The "next" cursor is passed as a query param to get the next page.
//   IntersectionObserver in InfiniteScrollList triggers fetchNextPage().

import {
    useInfiniteQuery,
    useMutation,
    useQueryClient,
    type InfiniteData,
  } from '@tanstack/react-query';
  import { feedApi, postsApi } from '@qommunity/api-client';
  import type { FeedPage, FeedItem } from '@qommunity/types';
  import { queryKeys } from './queryKeys';
  
  // ─── Home feed ────────────────────────────────────────────────────────────────
  export function useHomeFeed() {
    return useInfiniteQuery<FeedPage, Error, InfiniteData<FeedPage>, ReturnType<typeof queryKeys.feed.home>, string | undefined>({
      queryKey: queryKeys.feed.home(),
      queryFn: ({ pageParam }) => feedApi.getHomeFeed(pageParam),
      initialPageParam: undefined,
      getNextPageParam: (lastPage) => lastPage.next ?? undefined,
      staleTime: 30_000,  // Feed data fresh for 30s — matches backend Redis TTL
    });
  }
  
  // ─── Explore feed ─────────────────────────────────────────────────────────────
  export function useExploreFeed() {
    return useInfiniteQuery<FeedPage, Error, InfiniteData<FeedPage>, ReturnType<typeof queryKeys.feed.explore>, string | undefined>({
      queryKey: queryKeys.feed.explore(),
      queryFn: ({ pageParam }) => feedApi.getExploreFeed(pageParam),
      initialPageParam: undefined,
      getNextPageParam: (lastPage) => lastPage.next ?? undefined,
      staleTime: 60_000,
    });
  }
  
  // ─── Hashtag feed ─────────────────────────────────────────────────────────────
  export function useHashtagFeed(tag: string) {
    return useInfiniteQuery<FeedPage, Error, InfiniteData<FeedPage>, ReturnType<typeof queryKeys.feed.hashtag>, string | undefined>({
      queryKey: queryKeys.feed.hashtag(tag),
      queryFn: ({ pageParam }) => feedApi.getHashtagFeed(tag, pageParam),
      initialPageParam: undefined,
      getNextPageParam: (lastPage) => lastPage.next ?? undefined,
      enabled: tag.length > 0,
      staleTime: 60_000,
    });
  }
  
  // ─── Flatten pages → flat item array (used by components) ────────────────────
  export function flattenFeedPages(data: InfiniteData<FeedPage> | undefined): FeedItem[] {
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
  
      // onMutate fires BEFORE the API call — update the cache immediately
      onMutate: async ({ postId, isLiked }) => {
        // Cancel any outgoing refetches so they don't overwrite our optimistic update
        await queryClient.cancelQueries({ queryKey: queryKeys.feed.home() });
  
        // Snapshot the previous value for rollback
        const previousFeed = queryClient.getQueryData(queryKeys.feed.home());
  
        // Optimistically update every page that contains this post
        queryClient.setQueryData<InfiniteData<FeedPage>>(
          queryKeys.feed.home(),
          (old) => {
            if (!old) return old;
            return {
              ...old,
              pages: old.pages.map((page) => ({
                ...page,
                results: page.results.map((item) => {
                  if (item.post.id !== postId) return item;
                  return {
                    ...item,
                    post: {
                      ...item.post,
                      is_liked: !isLiked,
                      likes_count: isLiked
                        ? Math.max(0, item.post.likes_count - 1)
                        : item.post.likes_count + 1,
                    },
                  };
                }),
              })),
            };
          },
        );
  
        return { previousFeed };
      },
  
      // onError: roll back to snapshot if API fails
      onError: (_err, _vars, context) => {
        if (context?.previousFeed) {
          queryClient.setQueryData(queryKeys.feed.home(), context.previousFeed);
        }
      },
  
      // onSettled: always refetch to sync server truth after mutation
      onSettled: () => {
        void queryClient.invalidateQueries({ queryKey: queryKeys.feed.home() });
      },
    });
  }