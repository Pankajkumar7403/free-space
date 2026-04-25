// 📍 LOCATION: free-space/frontend/apps/web/src/app/(main)/explore/page.tsx

import type { Metadata } from 'next';
import { ExploreFeedList } from '@/components/features/feed/FeedList';

export const metadata: Metadata = {
  title: 'Search & Explore',
};

export default function ExplorePage() {
  return (
    <div className="mx-auto w-full max-w-[680px] px-0 sm:px-4 py-4 sm:py-6">
      <h1 className="sr-only">Explore</h1>
      <ExploreFeedList />
    </div>
  );
}
