// 📍 LOCATION: free-space/frontend/packages/hooks/src/useUsers.ts
//
// useUsers — TanStack Query hooks for user profiles and social graph.
//
// Key design decisions:
//   - useProfile caches per username (not UUID) because URLs use usernames
//   - Follow/unfollow uses optimistic updates — the button flips immediately
//   - useFollowers/useFollowing are infinite queries (large accounts have many)
//   - useUserSearch debounces at the component level, not here

import {
    useQuery,
    useMutation,
    useInfiniteQuery,
    useQueryClient,
    type InfiniteData,
  } from '@tanstack/react-query';
  import { usersApi } from '@qommunity/api-client';
  import type { User, UserSummary, PaginatedResponse } from '@qommunity/types';
  import { queryKeys } from './queryKeys';
  
  // ─── Current authenticated user profile ───────────────────────────────────────
  export function useMe() {
    return useQuery({
      queryKey: queryKeys.users.me(),
      queryFn:  usersApi.getMe,
      staleTime: 5 * 60 * 1000, // 5 min — own profile changes rarely
    });
  }
  
  // ─── Another user's public profile ───────────────────────────────────────────
  export function useProfile(username: string) {
    return useQuery({
      queryKey: queryKeys.users.profile(username),
      queryFn:  () => usersApi.getProfile(username),
      enabled:  username.length > 0,
      staleTime: 60_000,
    });
  }
  
  // ─── Followers list ───────────────────────────────────────────────────────────
  export function useFollowers(username: string) {
    return useInfiniteQuery<
      PaginatedResponse<UserSummary>,
      Error,
      InfiniteData<PaginatedResponse<UserSummary>>,
      ReturnType<typeof queryKeys.users.followers>,
      string | undefined
    >({
      queryKey: queryKeys.users.followers(username),
      queryFn:  ({ pageParam }) => usersApi.getFollowers(username, pageParam),
      initialPageParam: undefined,
      getNextPageParam: (page) => page.next ?? undefined,
      enabled:  username.length > 0,
    });
  }
  
  // ─── Following list ───────────────────────────────────────────────────────────
  export function useFollowing(username: string) {
    return useInfiniteQuery<
      PaginatedResponse<UserSummary>,
      Error,
      InfiniteData<PaginatedResponse<UserSummary>>,
      ReturnType<typeof queryKeys.users.following>,
      string | undefined
    >({
      queryKey: queryKeys.users.following(username),
      queryFn:  ({ pageParam }) => usersApi.getFollowing(username, pageParam),
      initialPageParam: undefined,
      getNextPageParam: (page) => page.next ?? undefined,
      enabled:  username.length > 0,
    });
  }
  
  // ─── User search ──────────────────────────────────────────────────────────────
  export function useUserSearch(query: string) {
    return useInfiniteQuery<
      PaginatedResponse<UserSummary>,
      Error,
      InfiniteData<PaginatedResponse<UserSummary>>,
      ReturnType<typeof queryKeys.users.search>,
      string | undefined
    >({
      queryKey: queryKeys.users.search(query),
      queryFn:  ({ pageParam }) => usersApi.searchUsers(query, pageParam),
      initialPageParam: undefined,
      getNextPageParam: (page) => page.next ?? undefined,
      enabled:  query.trim().length >= 1,
      staleTime: 30_000,
    });
  }
  
  // ─── Follow mutation with optimistic update ──────────────────────────────────
  export function useFollowUser() {
    const queryClient = useQueryClient();
  
    return useMutation({
      mutationFn: (username: string) => usersApi.followUser(username),
  
      onMutate: async (username) => {
        await queryClient.cancelQueries({ queryKey: queryKeys.users.profile(username) });
  
        const previousProfile = queryClient.getQueryData<User>(
          queryKeys.users.profile(username),
        );
  
        // Optimistically update follow state + follower count on the profile
        queryClient.setQueryData<User>(queryKeys.users.profile(username), (old) => {
          if (!old) return old;
          return {
            ...old,
            is_following:     true,
            followers_count:  old.followers_count + 1,
            follow_request_sent: old.account_privacy !== 'public' ? true : false,
          };
        });
  
        return { previousProfile, username };
      },
  
      onError: (_err, _username, context) => {
        if (context?.previousProfile) {
          queryClient.setQueryData(
            queryKeys.users.profile(context.username),
            context.previousProfile,
          );
        }
      },

      // Confirm with server payload — avoid refetching profile immediately (tests + MSW
      // may return stale is_following until backend contract is richer).
      onSuccess: (data, username) => {
        queryClient.setQueryData<User>(queryKeys.users.profile(username), (old) => {
          if (!old) return old;
          if (data.status === 'following') {
            return {
              ...old,
              is_following: true,
              follow_request_sent: false,
            };
          }
          return {
            ...old,
            is_following: false,
            follow_request_sent: true,
          };
        });
      },
    });
  }
  
  // ─── Unfollow mutation with optimistic update ────────────────────────────────
  export function useUnfollowUser() {
    const queryClient = useQueryClient();
  
    return useMutation({
      mutationFn: (username: string) => usersApi.unfollowUser(username),
  
      onMutate: async (username) => {
        await queryClient.cancelQueries({ queryKey: queryKeys.users.profile(username) });
  
        const previousProfile = queryClient.getQueryData<User>(
          queryKeys.users.profile(username),
        );
  
        queryClient.setQueryData<User>(queryKeys.users.profile(username), (old) => {
          if (!old) return old;
          return {
            ...old,
            is_following:        false,
            follow_request_sent: false,
            followers_count:     Math.max(0, old.followers_count - 1),
          };
        });
  
        return { previousProfile, username };
      },
  
      onError: (_err, _username, context) => {
        if (context?.previousProfile) {
          queryClient.setQueryData(
            queryKeys.users.profile(context.username),
            context.previousProfile,
          );
        }
      },

      onSuccess: (_void, username) => {
        void queryClient.invalidateQueries({ queryKey: queryKeys.feed.all() });
      },
    });
  }
  
  // ─── Block user ───────────────────────────────────────────────────────────────
  export function useBlockUser() {
    const queryClient = useQueryClient();
  
    return useMutation({
      mutationFn: (username: string) => usersApi.blockUser(username),
      onSuccess: (_data, username) => {
        // Remove blocked user from all caches immediately
        queryClient.removeQueries({ queryKey: queryKeys.users.profile(username) });
        // Invalidate feed — blocked user's posts should disappear
        void queryClient.invalidateQueries({ queryKey: queryKeys.feed.home() });
      },
    });
  }
  
  // ─── Mute user ────────────────────────────────────────────────────────────────
  export function useMuteUser() {
    const queryClient = useQueryClient();
  
    return useMutation({
      mutationFn: (username: string) => usersApi.muteUser(username),
      onSuccess: () => {
        void queryClient.invalidateQueries({ queryKey: queryKeys.feed.home() });
      },
    });
  }
  
  // ─── Update profile ───────────────────────────────────────────────────────────
  export function useUpdateProfile() {
    const queryClient = useQueryClient();
  
    return useMutation({
      mutationFn: usersApi.updateMe,
      onSuccess: (updatedUser) => {
        queryClient.setQueryData(queryKeys.users.me(), updatedUser);
        queryClient.setQueryData(
          queryKeys.users.profile(updatedUser.username),
          updatedUser,
        );
      },
    });
  }
  
  // ─── Helpers ─────────────────────────────────────────────────────────────────
  export function flattenUserPages(
    data: InfiniteData<PaginatedResponse<UserSummary>> | undefined,
  ): UserSummary[] {
    if (!data) return [];
    return data.pages.flatMap((page) => page.results);
  }