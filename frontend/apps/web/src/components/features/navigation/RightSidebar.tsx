// 📍 LOCATION: free-space/frontend/apps/web/src/components/features/navigation/RightSidebar.tsx
//
// Right sidebar: suggested users + trending hashtags.
// Populated in FM4 (Profile sprint) and FM7 (Explore sprint).
// For now renders a skeleton placeholder so the layout is complete.

import { Skeleton } from '@/components/ui/Skeleton';

export function RightSidebar() {
  return (
    <div className="space-y-6" aria-label="Suggested content">
      {/* Suggested users — populated in Sprint 9 (Social Graph) */}
      <section aria-labelledby="suggested-heading">
        <h2
          id="suggested-heading"
          className="text-sm font-semibold text-foreground mb-3"
        >
          Suggested for you
        </h2>
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex items-center gap-3">
              <Skeleton className="h-9 w-9 rounded-full" />
              <div className="flex-1 space-y-1.5">
                <Skeleton className="h-3 w-24" />
                <Skeleton className="h-2.5 w-16" />
              </div>
              <Skeleton className="h-7 w-16 rounded-full" />
            </div>
          ))}
        </div>
      </section>

      {/* Trending hashtags — populated in Sprint 14 (Explore) */}
      <section aria-labelledby="trending-heading">
        <h2
          id="trending-heading"
          className="text-sm font-semibold text-foreground mb-3"
        >
          Trending
        </h2>
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="space-y-1">
              <Skeleton className="h-3 w-28" />
              <Skeleton className="h-2.5 w-16" />
            </div>
          ))}
        </div>
      </section>

      {/* Footer links */}
      <p className="text-[10px] text-muted-foreground leading-relaxed">
        <span>© 2025 Qommunity · </span>
        <a href="/terms" className="hover:underline">Terms</a>
        {' · '}
        <a href="/privacy" className="hover:underline">Privacy</a>
        {' · '}
        <a href="/safety" className="hover:underline">Safety</a>
      </p>
    </div>
  );
}
