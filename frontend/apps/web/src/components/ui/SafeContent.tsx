// 📍 LOCATION: free-space/frontend/packages/ui-kit/src/components/SafeContent.tsx
//
// SafeContent — wraps potentially sensitive content.
// Shows a blur overlay with opt-in reveal for:
//   - Images from non-followers (safe messaging mode)
//   - ML-flagged sensitive content
//   - Community-reported content
// This is a first-class LGBTQ+ safety feature, not an afterthought.

'use client';

import * as React from 'react';
import { Eye, Shield } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SafeContentProps {
  /** Whether this content should be blurred */
  isBlurred: boolean;
  /** Reason for the blur — shown in the overlay */
  reason?: 'non_follower' | 'sensitive' | 'reported';
  /** The content to potentially blur */
  children: React.ReactNode;
  className?: string;
}

const REASON_COPY: Record<NonNullable<SafeContentProps['reason']>, { title: string; description: string }> = {
  non_follower: {
    title:       'Safe messaging mode',
    description: 'Media from people you don\'t follow is blurred for your safety.',
  },
  sensitive: {
    title:       'Sensitive content',
    description: 'This content has been flagged as potentially sensitive.',
  },
  reported: {
    title:       'Under review',
    description: 'This content has been reported and is under review.',
  },
};

export function SafeContent({
  isBlurred,
  reason = 'sensitive',
  children,
  className,
}: SafeContentProps) {
  const [revealed, setReveal] = React.useState(false);

  if (!isBlurred || revealed) {
    return <div className={className}>{children}</div>;
  }

  const copy = REASON_COPY[reason];

  return (
    <div className={cn('relative overflow-hidden rounded-xl', className)}>
      {/* Blurred content underneath */}
      <div className="blur-xl pointer-events-none select-none" aria-hidden="true">
        {children}
      </div>

      {/* Overlay */}
      <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-background/40 backdrop-blur-sm p-4">
        <div className="rounded-full bg-muted/80 p-2.5">
          <Shield className="h-5 w-5 text-muted-foreground" aria-hidden="true" />
        </div>
        <div className="text-center space-y-0.5">
          <p className="text-sm font-medium">{copy.title}</p>
          <p className="text-xs text-muted-foreground max-w-[200px]">{copy.description}</p>
        </div>
        {reason !== 'reported' && (
          <button
            onClick={() => setReveal(true)}
            className="inline-flex items-center gap-1.5 rounded-full px-4 py-1.5 text-xs font-medium bg-muted hover:bg-muted/80 transition-colors"
            aria-label="Show blurred content"
          >
            <Eye className="h-3.5 w-3.5" aria-hidden="true" />
            Show anyway
          </button>
        )}
      </div>
    </div>
  );
}
