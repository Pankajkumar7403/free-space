// 📍 LOCATION: free-space/frontend/packages/ui-kit/src/components/UserCard.tsx
//
// UserCard — compact user representation used in:
//   - Suggested users sidebar
//   - Followers/following lists
//   - Search results
//   - Comment author display
// Respects outing prevention — pronouns only shown if visibility allows.

import * as React from 'react';
import { CheckCircle2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { UserSummary } from '@qommunity/types';

interface UserCardProps {
  user: UserSummary;
  /** Viewer's relationship to this user — determines if pronouns are shown */
  viewerIsFollowing?: boolean;
  action?: React.ReactNode;
  onClick?: () => void;
  className?: string;
  /** Show a compact horizontal layout (for sidebar) vs full layout */
  compact?: boolean;
}

export function UserCard({
  user,
  viewerIsFollowing = false,
  action,
  onClick,
  className,
  compact = false,
}: UserCardProps) {
  // ── Outing prevention: only show pronouns to followers ─────────────────────
  const showPronouns =
    user.pronouns !== null &&
    (user.pronouns_visibility === 'public' ||
      (user.pronouns_visibility === 'followers_only' && viewerIsFollowing));

  const Wrapper = onClick ? 'button' : 'div';

  return (
    <Wrapper
      className={cn(
        'flex items-center gap-3 w-full text-left',
        onClick && 'hover:bg-muted/50 rounded-xl p-2 -mx-2 transition-colors cursor-pointer',
        className,
      )}
      onClick={onClick}
      {...(onClick ? { type: 'button' as const } : {})}
    >
      {/* Avatar placeholder — actual Avatar component from apps/web */}
      <div
        className={cn(
          'rounded-full bg-muted flex-shrink-0 overflow-hidden',
          compact ? 'h-9 w-9' : 'h-11 w-11',
        )}
        aria-hidden="true"
      >
        {user.avatar_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={user.avatar_url}
            alt=""
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center">
            <span className={cn('font-semibold text-primary', compact ? 'text-xs' : 'text-sm')}>
              {user.display_name[0]?.toUpperCase()}
            </span>
          </div>
        )}
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1">
          <span className={cn('font-semibold truncate', compact ? 'text-xs' : 'text-sm')}>
            {user.display_name}
          </span>
          {user.is_verified && (
            <CheckCircle2
              className={cn('text-primary flex-shrink-0', compact ? 'h-3 w-3' : 'h-3.5 w-3.5')}
              aria-label="Verified"
            />
          )}
        </div>
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className={cn('text-muted-foreground truncate', compact ? 'text-[10px]' : 'text-xs')}>
            @{user.username}
          </span>
          {showPronouns && (
            <span
              className={cn(
                'text-muted-foreground/60',
                compact ? 'text-[10px]' : 'text-xs',
              )}
              aria-label={`Pronouns: ${user.pronouns}`}
            >
              · {user.pronouns}
            </span>
          )}
        </div>
      </div>

      {/* Action slot */}
      {action && (
        <div className="flex-shrink-0" onClick={(e) => e.stopPropagation()}>
          {action}
        </div>
      )}
    </Wrapper>
  );
}
