// 📍 LOCATION: free-space/frontend/apps/web/src/components/features/feed/EmptyFeed.tsx
//
// EmptyFeed — shown when a feed has no posts.
// Default copy targets the home feed (new users); optional props customize for explore/hashtag.

import Link from 'next/link';
import { Users } from 'lucide-react';

export interface EmptyFeedProps {
  title?: string;
  description?: string;
  message?: string;
  ctaHref?: string;
  ctaLabel?: string;
  showCta?: boolean;
}

export function EmptyFeed({
  title = 'Your feed is empty',
  description,
  message,
  ctaHref = '/explore',
  ctaLabel = 'Explore the community',
  showCta = true,
}: EmptyFeedProps) {
  const body = message ?? description ?? 'Follow people in the community to see their posts here.';

  return (
    <div
      className="flex flex-col items-center justify-center py-24 px-6 text-center gap-5"
      role="status"
      aria-label="Empty feed"
    >
      <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center">
        <Users className="h-8 w-8 text-primary" aria-hidden="true" />
      </div>
      <div className="space-y-2">
        <p className="text-lg font-display font-semibold">{title}</p>
        <p className="text-sm text-muted-foreground max-w-[320px] mx-auto leading-relaxed">
          {body}
        </p>
      </div>
      {showCta && (
        <Link
          href={ctaHref}
          className="inline-flex items-center gap-2 rounded-xl px-6 py-3 text-sm font-semibold bg-primary text-white hover:bg-primary/90 transition-colors"
        >
          {ctaLabel}
        </Link>
      )}
    </div>
  );
}
