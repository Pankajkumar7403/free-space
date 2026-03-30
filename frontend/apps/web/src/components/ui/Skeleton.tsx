// 📍 LOCATION: free-space/frontend/apps/web/src/components/ui/Skeleton.tsx
//
// Used in all loading states. Matches exact component dimensions to prevent layout shift.

import { cn } from '@/lib/utils';

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {}

export function Skeleton({ className, ...props }: SkeletonProps) {
  return (
    <div
      className={cn('animate-skeleton-pulse rounded-md bg-muted', className)}
      aria-hidden="true"
      {...props}
    />
  );
}
