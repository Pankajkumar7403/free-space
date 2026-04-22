// 📍 LOCATION: free-space/frontend/apps/web/src/app/(main)/hashtag/[tag]/page.tsx

import type { Metadata } from 'next';
import { HashtagFeedList } from '@/components/features/feed/FeedList';

interface HashtagPageProps {
  params: Promise<{ tag: string }>;
}

export async function generateMetadata({ params }: HashtagPageProps): Promise<Metadata> {
  const { tag } = await params;
  const label = decodeURIComponent(tag);
  return {
    title: `#${label}`,
  };
}

export default async function HashtagPage({ params }: HashtagPageProps) {
  const { tag } = await params;
  const normalized = decodeURIComponent(tag).replace(/^#/, '');

  return (
    <div className="mx-auto w-full max-w-[680px] px-0 sm:px-4 py-4 sm:py-6">
      <h1 className="px-4 sm:px-0 text-lg font-display font-semibold mb-4">
        #{normalized}
      </h1>
      <HashtagFeedList tag={normalized} />
    </div>
  );
}
