// 📍 LOCATION: free-space/frontend/apps/web/src/components/features/feed/FeedList.tsx
//
// FeedList — renders the home feed as an infinite-scroll list of PostCards.
//
// Data flow:
//   1. useHomeFeed() fetches page 1 from /api/v1/feed/
//   2. IntersectionObserver sentinel triggers fetchNextPage() when scrolled near bottom
//   3. New pages append to the existing list without re-rendering previous items
//   4. Each PostCard receives a single Post prop — no prop drilling beyond that
//
// Error and empty states are handled here, not in PostCard.

'use client';

import { useRef, useEffect, useCallback } from 'react';
import { useHomeFeed, flattenFeedPages } from '@qommunity/hooks';
import { PostCard } from './PostCard';
import { FeedSkeleton } from './PostCardSkeleton';
import { EmptyFeed } from './EmptyFeed';
import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface FeedListProps {
  onCommentClick?: (postId: string) => void;
}

export function FeedList({ onCommentClick }: FeedListProps) {
  const {
    data,
    isLoading,
    isError,
    isFetchingNextPage,
    hasNextPage,
    fetchNextPage,
    refetch,
  } = useHomeFeed();

  const sentinelRef = useRef<HTMLDivElement>(null);

  // ── IntersectionObserver: load next page when sentinel is visible ──────────
  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel || !hasNextPage || isFetchingNextPage) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) {
          void fetchNextPage();
        }
      },
      {
        threshold: 0.1,
        rootMargin: '300px', // Pre-fetch 300px before user reaches bottom
      },
    );

    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

  const posts = flattenFeedPages(data);

  // ── Loading state (first page) ─────────────────────────────────────────────
  if (isLoading) {
    return <FeedSkeleton count={4} />;
  }

  // ── Error state ────────────────────────────────────────────────────────────
  if (isError) {
    return (
      <div className="flex flex-col items-center py-20 gap-4 text-center px-4">
        <p className="text-base font-semibold">Could not load feed</p>
        <p className="text-sm text-muted-foreground">
          Something went wrong. Please check your connection and try again.
        </p>
        <button
          onClick={() => void refetch()}
          className="rounded-lg px-4 py-2 text-sm font-medium bg-primary text-white hover:bg-primary/90 transition-colors"
        >
          Try again
        </button>
      </div>
    );
  }

  // ── Empty state ────────────────────────────────────────────────────────────
  if (posts.length === 0) {
    return <EmptyFeed />;
  }

  return (
    <div
      className="w-full"
      role="feed"
      aria-label="Home feed"
      aria-busy={isFetchingNextPage}
    >
      {posts.map((item) => (
        <PostCard
          key={item.post.id}
          post={item.post}
          onCommentClick={onCommentClick}
        />
      ))}

      {/* Sentinel element — triggers next page load when visible */}
      {hasNextPage && (
        <div
          ref={sentinelRef}
          className="h-4"
          aria-hidden="true"
        />
      )}

      {/* Loading spinner for subsequent pages */}
      {isFetchingNextPage && (
        <div
          className="flex justify-center py-8"
          role="status"
          aria-label="Loading more posts"
        >
          <Loader2
            className="h-5 w-5 animate-spin text-muted-foreground"
            aria-hidden="true"
          />
        </div>
      )}

      {/* End of feed message */}
      {!hasNextPage && posts.length > 0 && (
        <div className="py-12 text-center">
          <p className="text-xs text-muted-foreground select-none">
            You are all caught up! Check back later. 🏳️‍🌈
          </p>
        </div>
      )}
    </div>
  );
}