// 📍 LOCATION: free-space/frontend/apps/web/src/app/(main)/feed/page.tsx
// Home feed page (Sprint 5 shell): renders feed list with
// loading/empty/error handled in FeedList.

import type { Metadata } from 'next';
import { FeedList } from '@/components/features/feed/FeedList';

export const metadata: Metadata = {
  title: 'Home',
};

export default function FeedPage() {
  return (
    <div className="mx-auto w-full max-w-[680px] px-0 sm:px-4 py-4 sm:py-6">
      <FeedList />
    </div>
  );
}
