// 📍 LOCATION: free-space/frontend/packages/ui-kit/src/components/InfiniteScrollList.tsx
//
// InfiniteScrollList — wraps TanStack Query's useInfiniteQuery.
// Used for: home feed, profile posts grid, comment list, notification list.
// Uses IntersectionObserver to trigger next page fetch — no scroll listener.

'use client';

import * as React from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface InfiniteScrollListProps<T> {
  /** All items across all fetched pages */
  items: T[];
  /** Render function for each item */
  renderItem: (item: T, index: number) => React.ReactNode;
  /** Whether more pages are available */
  hasNextPage: boolean;
  /** Whether a page fetch is in progress */
  isFetchingNextPage: boolean;
  /** Call to load the next page */
  fetchNextPage: () => void;
  /** Whether the initial load is in progress */
  isLoading?: boolean;
  /** Skeleton placeholder shown during initial load */
  skeleton?: React.ReactNode;
  /** Shown when items array is empty and not loading */
  emptyState?: React.ReactNode;
  /** Shown when an error occurs */
  errorState?: React.ReactNode;
  className?: string;
  /** aria-label for the list */
  label?: string;
}

export function InfiniteScrollList<T>({
  items,
  renderItem,
  hasNextPage,
  isFetchingNextPage,
  fetchNextPage,
  isLoading = false,
  skeleton,
  emptyState,
  errorState,
  className,
  label,
}: InfiniteScrollListProps<T>) {
  // ─── Intersection observer sentinel ────────────────────────────────────────
  const sentinelRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel || !hasNextPage || isFetchingNextPage) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) {
          fetchNextPage();
        }
      },
      { threshold: 0.1, rootMargin: '200px' }, // Pre-fetch 200px before sentinel is visible
    );

    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

  // ─── Render states ─────────────────────────────────────────────────────────
  if (isLoading && skeleton) {
    return <>{skeleton}</>;
  }

  if (!isLoading && items.length === 0) {
    return <>{emptyState}</> ?? null;
  }

  return (
    <div className={cn('w-full', className)} aria-label={label}>
      {items.map((item, index) => (
        <React.Fragment key={index}>
          {renderItem(item, index)}
        </React.Fragment>
      ))}

      {/* Sentinel — triggers next page when scrolled into view */}
      {hasNextPage && (
        <div ref={sentinelRef} className="h-4" aria-hidden="true" />
      )}

      {/* Loading spinner for subsequent pages */}
      {isFetchingNextPage && (
        <div className="flex justify-center py-6" aria-label="Loading more" role="status">
          <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" aria-hidden="true" />
        </div>
      )}

      {/* End of list message */}
      {!hasNextPage && items.length > 0 && (
        <p className="text-center text-xs text-muted-foreground py-8 select-none">
          You&apos;ve seen it all 🏳️‍🌈
        </p>
      )}
    </div>
  );
}
