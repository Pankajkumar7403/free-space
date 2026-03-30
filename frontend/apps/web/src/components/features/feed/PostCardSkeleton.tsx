// 📍 LOCATION: free-space/frontend/apps/web/src/components/features/feed/PostCardSkeleton.tsx
//
// PostCardSkeleton — pixel-perfect loading placeholder for PostCard.
// Dimensions match the real PostCard so there is zero layout shift
// when content loads in. Uses Skeleton component with pulse animation.

import { Skeleton } from '@/components/ui/Skeleton';

export function PostCardSkeleton() {
  return (
    <article
      className="border-b border-border bg-background py-4 px-0 sm:px-4 sm:rounded-xl sm:border sm:mb-3"
      aria-hidden="true"
    >
      {/* Header */}
      <div className="flex items-start justify-between px-4 sm:px-0 mb-3">
        <div className="flex items-center gap-3">
          <Skeleton className="h-10 w-10 rounded-full flex-shrink-0" />
          <div className="space-y-1.5">
            <Skeleton className="h-3.5 w-28" />
            <Skeleton className="h-3 w-20" />
          </div>
        </div>
        <Skeleton className="h-8 w-8 rounded-lg" />
      </div>

      {/* Content text lines */}
      <div className="px-4 sm:px-0 mb-3 space-y-2">
        <Skeleton className="h-3.5 w-full" />
        <Skeleton className="h-3.5 w-4/5" />
        <Skeleton className="h-3.5 w-3/5" />
      </div>

      {/* Media placeholder */}
      <Skeleton className="w-full aspect-square sm:aspect-[4/3] sm:rounded-xl mb-3" />

      {/* Action bar */}
      <div className="flex items-center gap-3 px-4 sm:px-0">
        <Skeleton className="h-8 w-16 rounded-lg" />
        <Skeleton className="h-8 w-16 rounded-lg" />
        <Skeleton className="h-8 w-8 rounded-lg" />
        <div className="flex-1" />
        <Skeleton className="h-8 w-8 rounded-lg" />
      </div>
    </article>
  );
}

// ─── Multiple skeletons for initial load ──────────────────────────────────────
export function FeedSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div aria-label="Loading feed" role="status">
      {Array.from({ length: count }).map((_, i) => (
        <PostCardSkeleton key={i} />
      ))}
      <span className="sr-only">Loading posts...</span>
    </div>
  );
}