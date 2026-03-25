// 📍 LOCATION: free-space/frontend/apps/web/src/app/(main)/feed/page.tsx
//
// Home feed page — Sprint 3 will build FeedList + PostCard here.
// For now: layout stub so routing works end-to-end.

import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Home',
};

export default function FeedPage() {
  return (
    <div className="feed-container py-6">
      <p className="text-center text-muted-foreground text-sm py-20">
        Feed coming in Sprint 3 🏳️‍🌈
      </p>
    </div>
  );
}
