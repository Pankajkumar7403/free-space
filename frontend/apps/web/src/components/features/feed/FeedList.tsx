// 📍 LOCATION: free-space/frontend/apps/web/src/components/features/feed/FeedList.tsx
//
// Feed list variants share one implementation (FeedListView):
//   - Home: useHomeFeed → /api/v1/feed/
//   - Explore: useExploreFeed → /api/v1/feed/explore/
//   - Hashtag: useHashtagFeed(tag) → /api/v1/feed/hashtag/{tag}/

'use client';

import { useRef, useEffect } from 'react';
import {
  useHomeFeed,
  useExploreFeed,
  useHashtagFeed,
  flattenFeedPages,
} from '@/hooks';
import { PostCard } from './PostCard';
import { FeedSkeleton } from './PostCardSkeleton';
import { EmptyFeed } from './EmptyFeed';
import { Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/Button';

/** Shared slice of infinite feed query state (home / explore / hashtag). */
export type InfiniteFeedQuery = Pick<
  ReturnType<typeof useHomeFeed>,
  | 'data'
  | 'isLoading'
  | 'isError'
  | 'isFetchingNextPage'
  | 'hasNextPage'
  | 'fetchNextPage'
  | 'refetch'
>;

interface FeedListViewProps {
  query: InfiniteFeedQuery;
  onCommentClick?: (postId: string) => void;
  /** Accessible label for the feed region */
  ariaLabel: string;
  /** Optional empty state (e.g. explore / hashtag); home feed uses EmptyFeed defaults */
  emptyTitle?: string;
  emptyMessage?: string;
  emptyShowCta?: boolean;
}

export function FeedListView({
  query,
  onCommentClick,
  ariaLabel,
  emptyTitle,
  emptyMessage,
  emptyShowCta,
}: FeedListViewProps) {
  const {
    data,
    isLoading,
    isError,
    isFetchingNextPage,
    hasNextPage,
    fetchNextPage,
    refetch,
  } = query;

  const sentinelRef = useRef<HTMLDivElement>(null);

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
        rootMargin: '300px',
      },
    );

    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

  const posts = flattenFeedPages(data);

  if (isLoading) {
    return <FeedSkeleton count={4} />;
  }

  if (isError) {
    return (
      <div className="flex flex-col items-center py-20 gap-4 text-center px-4">
        <p className="text-base font-semibold">Could not load feed</p>
        <p className="text-sm text-muted-foreground">
          Something went wrong. Please check your connection and try again.
        </p>
        <Button type="button" variant="default" onClick={() => void refetch()}>
          Try again
        </Button>
      </div>
    );
  }

  if (posts.length === 0) {
    if (emptyMessage !== undefined || emptyTitle !== undefined) {
      return (
        <EmptyFeed
          title={emptyTitle ?? 'Nothing to show yet'}
          message={emptyMessage ?? 'Try again later or explore other tags.'}
          showCta={emptyShowCta ?? true}
        />
      );
    }
    return <EmptyFeed />;
  }

  return (
    <div
      className="w-full"
      role="feed"
      aria-label={ariaLabel}
      aria-busy={isFetchingNextPage}
    >
      {posts.map((item) => (
        <PostCard
          key={item.id}
          post={item}
          onCommentClick={onCommentClick}
        />
      ))}

      {hasNextPage && (
        <div ref={sentinelRef} className="h-4" aria-hidden="true" />
      )}

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

      {!hasNextPage && posts.length > 0 && (
        <div className="py-12 text-center">
          <p className="text-xs text-muted-foreground select-none">
            You are all caught up! Check back later.
          </p>
        </div>
      )}
    </div>
  );
}

interface FeedListProps {
  onCommentClick?: (postId: string) => void;
}

export function FeedList({ onCommentClick }: FeedListProps) {
  const query = useHomeFeed();
  return (
    <FeedListView
      query={query}
      onCommentClick={onCommentClick}
      ariaLabel="Home feed"
    />
  );
}

export function ExploreFeedList({ onCommentClick }: FeedListProps) {
  const query = useExploreFeed();
  return (
    <FeedListView
      query={query}
      onCommentClick={onCommentClick}
      ariaLabel="Explore feed"
      emptyTitle="Explore is quiet"
      emptyMessage="No posts here yet. Check back soon."
    />
  );
}

interface HashtagFeedListProps extends FeedListProps {
  tag: string;
}

export function HashtagFeedList({ tag, onCommentClick }: HashtagFeedListProps) {
  const query = useHashtagFeed(tag);
  return (
    <FeedListView
      query={query}
      onCommentClick={onCommentClick}
      ariaLabel={`Posts tagged ${tag}`}
      emptyTitle={`#${tag}`}
      emptyMessage={`No posts for #${tag} yet.`}
      emptyShowCta
    />
  );
}
