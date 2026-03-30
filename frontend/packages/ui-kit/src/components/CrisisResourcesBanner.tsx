// 📍 LOCATION: free-space/frontend/packages/ui-kit/src/components/CrisisResourcesBanner.tsx
//
// CrisisResourcesBanner — surfaced in feed when backend triggers a keyword match.
// This is a critical LGBTQ+ safety feature (FM8 roadmap item).
// Displayed non-alarmingly: supportive, not clinical.

import * as React from 'react';
import { X, Heart } from 'lucide-react';
import { cn } from '../lib/cn';

interface CrisisResource {
  name: string;
  description: string;
  phone?: string;
  url: string;
  /** e.g. 'LGBTQ+ youth', 'Trans community', 'General crisis' */
  audience: string;
}

// Resources are hardcoded — not fetched from API to ensure always-available
const RESOURCES: CrisisResource[] = [
  {
    name:        'The Trevor Project',
    description: '24/7 crisis support for LGBTQ+ young people',
    phone:       '1-866-488-7386',
    url:         'https://www.thetrevorproject.org',
    audience:    'LGBTQ+ youth',
  },
  {
    name:        'Trans Lifeline',
    description: 'Peer support hotline run by and for trans people',
    phone:       '877-565-8860',
    url:         'https://translifeline.org',
    audience:    'Trans community',
  },
  {
    name:        '988 Suicide & Crisis Lifeline',
    description: 'Free, confidential support — call or text 988',
    phone:       '988',
    url:         'https://988lifeline.org',
    audience:    'Everyone',
  },
];

interface CrisisResourcesBannerProps {
  onDismiss?: () => void;
  className?: string;
}

export function CrisisResourcesBanner({ onDismiss, className }: CrisisResourcesBannerProps) {
  return (
    <div
      className={cn(
        'rounded-2xl border border-primary/20 bg-primary/5 p-4 space-y-3',
        className,
      )}
      role="region"
      aria-label="Support resources"
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <Heart className="h-4 w-4 text-primary flex-shrink-0" aria-hidden="true" />
          <p className="text-sm font-semibold text-foreground">
            You&apos;re not alone
          </p>
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="rounded-md p-0.5 text-muted-foreground hover:text-foreground transition-colors"
            aria-label="Dismiss support resources"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        )}
      </div>

      <p className="text-xs text-muted-foreground leading-relaxed">
        We care about you. If you&apos;re going through a difficult time, these free
        and confidential resources are here to help.
      </p>

      {/* Resource cards */}
      <div className="space-y-2">
        {RESOURCES.map((resource) => (
          <a
            key={resource.name}
            href={resource.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-start justify-between gap-3 rounded-xl bg-background/60 p-3 hover:bg-background/80 transition-colors group"
            aria-label={`${resource.name} — ${resource.description}`}
          >
            <div className="space-y-0.5">
              <p className="text-xs font-semibold text-foreground group-hover:text-primary transition-colors">
                {resource.name}
              </p>
              <p className="text-[11px] text-muted-foreground">{resource.description}</p>
              <span className="inline-block text-[10px] bg-primary/10 text-primary rounded-full px-2 py-px">
                {resource.audience}
              </span>
            </div>
            {resource.phone && (
              <span className="text-xs font-mono font-medium text-primary flex-shrink-0 mt-0.5">
                {resource.phone}
              </span>
            )}
          </a>
        ))}
      </div>
    </div>
  );
}
