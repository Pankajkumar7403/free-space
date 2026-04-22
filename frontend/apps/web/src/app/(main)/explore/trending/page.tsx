// 📍 LOCATION: free-space/frontend/apps/web/src/app/(main)/explore/trending/page.tsx
//
// Trending uses the same explore feed until a dedicated trending API exists.

import type { Metadata } from 'next';
import { ExploreFeedList } from '@/components/features/feed/FeedList';

export const metadata: Metadata = {
  title: 'Trending',
};

export default function TrendingPage() {
  return (
    <div className="mx-auto w-full max-w-[680px] px-0 sm:px-4 py-4 sm:py-6">
      <h1 className="px-4 sm:px-0 text-lg font-display font-semibold mb-4">Trending</h1>
      <ExploreFeedList />
    </div>
  );
}
