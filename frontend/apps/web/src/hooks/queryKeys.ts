// 📍 LOCATION: free-space/frontend/packages/hooks/src/queryKeys.ts
//
// Centralised TanStack Query key factory.
// Every query key in the app comes from here — never inline strings.
//
// WHY: When you invalidate a query, you need the exact same key array.
// Centralising keys prevents cache misses from typos and makes
// cache invalidation predictable. This mirrors the backend's
// selectors.py pattern — one place for all read operations.

export const queryKeys = {
    // ─── Feed ──────────────────────────────────────────────────────────────────
    feed: {
      all:     ()              => ['feed']                    as const,
      home:    ()              => ['feed', 'home']            as const,
      explore: ()              => ['feed', 'explore']         as const,
      hashtag: (tag: string)   => ['feed', 'hashtag', tag]   as const,
    },
  
    // ─── Posts ─────────────────────────────────────────────────────────────────
    posts: {
      all:        ()               => ['posts']                        as const,
      detail:     (id: string)     => ['posts', 'detail', id]         as const,
      byUser:     (username: string) => ['posts', 'user', username]   as const,
      likes:      (id: string)     => ['posts', 'likes', id]          as const,
    },
  
    // ─── Users ─────────────────────────────────────────────────────────────────
    users: {
      all:        ()               => ['users']                        as const,
      me:         ()               => ['users', 'me']                 as const,
      profile:    (username: string) => ['users', 'profile', username] as const,
      followers:  (username: string) => ['users', 'followers', username] as const,
      following:  (username: string) => ['users', 'following', username] as const,
      search:     (query: string)  => ['users', 'search', query]      as const,
    },
  
    // ─── Comments ──────────────────────────────────────────────────────────────
    comments: {
      all:      ()                           => ['comments']                        as const,
      byPost:   (postId: string)             => ['comments', 'post', postId]        as const,
      replies:  (commentId: string)          => ['comments', 'replies', commentId]  as const,
    },
  
    // ─── Notifications ─────────────────────────────────────────────────────────
    notifications: {
      all:         () => ['notifications']             as const,
      list:        () => ['notifications', 'list']     as const,
      unreadCount: () => ['notifications', 'unread']   as const,
    },
  } as const;