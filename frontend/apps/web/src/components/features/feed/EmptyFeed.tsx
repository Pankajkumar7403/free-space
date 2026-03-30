// 📍 LOCATION: free-space/frontend/apps/web/src/components/features/feed/EmptyFeed.tsx
//
// EmptyFeed — shown when a user has no posts in their feed yet.
// This happens for brand-new accounts who have not followed anyone.
// Guides them toward finding people to follow.

import Link from 'next/link';
import { Users } from 'lucide-react';

export function EmptyFeed() {
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
        <p className="text-lg font-display font-semibold">Your feed is empty</p>
        <p className="text-sm text-muted-foreground max-w-[280px] mx-auto leading-relaxed">
          Follow people in the community to see their posts here.
        </p>
      </div>
      <Link
        href="/explore"
        className="inline-flex items-center gap-2 rounded-xl px-6 py-3 text-sm font-semibold bg-primary text-white hover:bg-primary/90 transition-colors"
      >
        Explore the community
      </Link>
    </div>
  );
}