// 📍 LOCATION: free-space/frontend/apps/web/src/components/features/profile/ProfileHeader.tsx
//
// ProfileHeader — top section of a user's profile page.
// Contains: avatar (with optional pride ring), stats, bio, identity fields,
// follow button, and options dropdown.
//
// LGBTQ+ safety rules applied here:
//   - Pronouns: shown only per visibility setting
//   - Gender identity: shown only per visibility setting
//   - Sexual orientation: shown only per visibility setting
//   - All three are hidden from non-followers by default (outing prevention)

'use client';

import Link from 'next/link';
import { Globe, MapPin, MoreHorizontal } from 'lucide-react';

import type { User } from '@qommunity/types';
import { formatCount } from '@/lib/utils';
import { Avatar } from '@/components/ui/Avatar';
import { Button } from '@/components/ui/Button';
import { Skeleton } from '@/components/ui/Skeleton';
import {
  DropdownMenu, DropdownMenuContent,
  DropdownMenuItem, DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/DropdownMenu';
import { FollowButton } from './FollowButton';
import { useAuthStore } from '@/stores/authStore';
import { useBlockUser, useMuteUser } from '@qommunity/hooks';
import { useToast } from '@/components/ui/Toast';

interface ProfileHeaderProps {
  user: User;
  isOwnProfile: boolean;
}

export function ProfileHeader({ user, isOwnProfile }: ProfileHeaderProps) {
  const currentUser  = useAuthStore((s) => s.user);
  const blockUser    = useBlockUser();
  const muteUser     = useMuteUser();
  const { toast }    = useToast();

  // ── Outing prevention: compute visibility for each identity field ──────────
  const isFollowing      = user.is_following ?? false;
  const canSeePrivate    = isOwnProfile || isFollowing;

  const showPronouns = user.pronouns && (
    user.pronouns_visibility === 'public' ||
    (user.pronouns_visibility === 'followers_only' && canSeePrivate)
  );

  const showGenderIdentity = user.gender_identity && (
    user.gender_identity_visibility === 'public' ||
    (user.gender_identity_visibility === 'followers_only' && canSeePrivate)
  );

  const showSexualOrientation = user.sexual_orientation && (
    user.sexual_orientation_visibility === 'public' ||
    (user.sexual_orientation_visibility === 'followers_only' && canSeePrivate)
  );

  const handleBlock = () => {
    blockUser.mutate(user.username, {
      onSuccess: () => toast({ title: `${user.display_name} blocked`, variant: 'success' }),
      onError:   () => toast({ title: 'Could not block user', variant: 'error' }),
    });
  };

  const handleMute = () => {
    muteUser.mutate(user.username, {
      onSuccess: () => toast({ title: `${user.display_name} muted`, variant: 'success' }),
      onError:   () => toast({ title: 'Could not mute user', variant: 'error' }),
    });
  };

  return (
    <div className="px-4 pt-6 pb-4 space-y-4">
      {/* Top row: avatar + stats + actions */}
      <div className="flex items-start gap-6">
        {/* Avatar — pride ring for own profile */}
        <div className="flex-shrink-0">
          <Avatar
            src={user.avatar_url}
            alt={user.display_name}
            size="2xl"
            prideRing={isOwnProfile}
          />
        </div>

        {/* Stats + actions */}
        <div className="flex-1 min-w-0 space-y-3 pt-1">
          {/* Username + options */}
          <div className="flex items-center gap-2 flex-wrap">
            <h1 className="text-xl font-display font-bold truncate">
              {user.display_name}
            </h1>
            <span className="text-sm text-muted-foreground">@{user.username}</span>

            {!isOwnProfile && (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon-sm"
                    aria-label="More options"
                    className="text-muted-foreground ml-auto"
                  >
                    <MoreHorizontal className="h-4 w-4" aria-hidden="true" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onSelect={handleMute}>
                    Mute @{user.username}
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem destructive onSelect={handleBlock}>
                    Block @{user.username}
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem destructive>
                    Report @{user.username}
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            )}
          </div>

          {/* Stats: posts / followers / following */}
          <div className="flex gap-5">
            <Stat label="posts"     value={user.posts_count}     />
            <Link href={`/${user.username}/followers`} className="hover:opacity-70 transition-opacity">
              <Stat label="followers" value={user.followers_count} />
            </Link>
            <Link href={`/${user.username}/following`} className="hover:opacity-70 transition-opacity">
              <Stat label="following" value={user.following_count} />
            </Link>
          </div>

          {/* Follow button */}
          <FollowButton user={user} />
        </div>
      </div>

      {/* Bio section */}
      <div className="space-y-2">
        {user.bio && (
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{user.bio}</p>
        )}

        {/* Identity fields — outing-prevention-aware */}
        {(showPronouns || showGenderIdentity || showSexualOrientation) && (
          <div className="flex flex-wrap gap-1.5">
            {showPronouns && (
              <span className="inline-flex items-center rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-medium text-primary">
                {user.pronouns}
              </span>
            )}
            {showGenderIdentity && (
              <span className="inline-flex items-center rounded-full bg-secondary/10 px-2.5 py-0.5 text-xs font-medium text-secondary">
                {user.gender_identity?.replace(/_/g, ' ')}
              </span>
            )}
            {showSexualOrientation && (
              <span className="inline-flex items-center rounded-full bg-accent/10 px-2.5 py-0.5 text-xs font-medium text-accent">
                {user.sexual_orientation?.replace(/_/g, ' ')}
              </span>
            )}
          </div>
        )}

        {/* Website + location */}
        <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
          {user.website && (
            <a
              href={user.website}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 hover:text-primary transition-colors"
            >
              <Globe className="h-3.5 w-3.5" aria-hidden="true" />
              {user.website.replace(/^https?:\/\//, '')}
            </a>
          )}
        </div>
      </div>

      {/* Private account notice for non-followers */}
      {user.account_privacy === 'private' && !canSeePrivate && (
        <div className="rounded-xl border border-border bg-muted/30 p-4 text-center">
          <p className="text-sm font-medium">This account is private</p>
          <p className="text-xs text-muted-foreground mt-1">
            Follow to see their posts.
          </p>
        </div>
      )}
    </div>
  );
}

// ─── Stat cell ────────────────────────────────────────────────────────────────
function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="text-center">
      <p className="text-base font-bold tabular-nums">{formatCount(value)}</p>
      <p className="text-xs text-muted-foreground">{label}</p>
    </div>
  );
}

// ─── Skeleton ─────────────────────────────────────────────────────────────────
export function ProfileHeaderSkeleton() {
  return (
    <div className="px-4 pt-6 pb-4 space-y-4">
      <div className="flex items-start gap-6">
        <Skeleton className="h-28 w-28 rounded-full flex-shrink-0" />
        <div className="flex-1 space-y-3 pt-1">
          <div className="space-y-1.5">
            <Skeleton className="h-5 w-36" />
            <Skeleton className="h-4 w-24" />
          </div>
          <div className="flex gap-5">
            <Skeleton className="h-10 w-14" />
            <Skeleton className="h-10 w-14" />
            <Skeleton className="h-10 w-14" />
          </div>
          <Skeleton className="h-10 w-28 rounded-xl" />
        </div>
      </div>
      <div className="space-y-2">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4" />
      </div>
    </div>
  );
}