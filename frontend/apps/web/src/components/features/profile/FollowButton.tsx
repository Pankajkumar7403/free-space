// 📍 LOCATION: free-space/frontend/apps/web/src/components/features/profile/FollowButton.tsx
//
// FollowButton — handles all four follow states:
//   1. Not following        → "Follow" button (blue)
//   2. Follow requested     → "Requested" button (outline) for private accounts
//   3. Following            → "Following" button (outline, shows "Unfollow" on hover)
//   4. Own profile          → "Edit profile" button
//
// Uses optimistic updates — button flips immediately without waiting for API.
// Rolls back on error and shows a toast.

'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Loader2, UserCheck, UserMinus, UserPlus, Clock } from 'lucide-react';

import { useFollowUser, useUnfollowUser, queryKeys } from '@qommunity/hooks';
import { usersApi } from '@qommunity/api-client';
import type { User } from '@qommunity/types';

import { useAuthStore } from '@/stores/authStore';
import { useToast } from '@/components/ui/Toast';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils';

interface FollowButtonProps {
  user: User;
  size?: 'sm' | 'default';
  className?: string;
}

export function FollowButton({ user, size = 'default', className }: FollowButtonProps) {
  const currentUser  = useAuthStore((s) => s.user);
  const { toast }    = useToast();
  const followUser   = useFollowUser();
  const unfollowUser = useUnfollowUser();

  const [isHoveringFollow, setIsHoveringFollow] = useState(false);

  // Profile query merges server fetches with optimistic follow/unfollow cache updates.
  const { data: profile = user } = useQuery({
    queryKey: queryKeys.users.profile(user.username),
    queryFn: () => usersApi.getProfile(user.username),
    initialData: user,
    staleTime: 60_000,
    refetchOnMount: false,
    refetchOnWindowFocus: false,
  });

  // Own profile — render edit button instead
  if (currentUser?.username === profile.username) {
    return (
      <Button
        variant="outline"
        size={size}
        className={className}
        onClick={() => { /* navigate to /settings/profile — Sprint 7 */ }}
      >
        Edit profile
      </Button>
    );
  }

  const isPending = followUser.isPending || unfollowUser.isPending;

  const handleFollow = () => {
    followUser.mutate(profile.username, {
      onError: () => {
        toast({
          title: 'Could not follow',
          description: 'Please try again.',
          variant: 'error',
        });
      },
    });
  };

  const handleUnfollow = () => {
    unfollowUser.mutate(profile.username, {
      onError: () => {
        toast({
          title: 'Could not unfollow',
          description: 'Please try again.',
          variant: 'error',
        });
      },
    });
  };

  // ── State: Following ──────────────────────────────────────────────────────
  if (profile.is_following) {
    return (
      <Button
        variant="outline"
        size={size}
        className={cn(
          'min-w-[100px] transition-all',
          isHoveringFollow && 'border-destructive text-destructive hover:bg-destructive/5',
          className,
        )}
        disabled={isPending}
        onClick={handleUnfollow}
        onMouseEnter={() => setIsHoveringFollow(true)}
        onMouseLeave={() => setIsHoveringFollow(false)}
        aria-label={isHoveringFollow ? 'Unfollow' : 'Following'}
      >
        {isPending ? (
          <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
        ) : isHoveringFollow ? (
          <>
            <UserMinus className="h-4 w-4 mr-1.5" aria-hidden="true" />
            Unfollow
          </>
        ) : (
          <>
            <UserCheck className="h-4 w-4 mr-1.5" aria-hidden="true" />
            Following
          </>
        )}
      </Button>
    );
  }

  // ── State: Follow requested (private account) ─────────────────────────────
  if (profile.follow_request_sent) {
    return (
      <Button
        variant="outline"
        size={size}
        className={cn('min-w-[100px]', className)}
        disabled={isPending}
        onClick={handleUnfollow} // cancels the request
        aria-label="Requested — cancel follow request"
      >
        {isPending ? (
          <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
        ) : (
          <>
            <Clock className="h-4 w-4 mr-1.5" aria-hidden="true" />
            Requested
          </>
        )}
      </Button>
    );
  }

  // ── State: Not following ──────────────────────────────────────────────────
  return (
    <Button
      size={size}
      className={cn('min-w-[100px]', className)}
      disabled={isPending}
      onClick={handleFollow}
      aria-label={`Follow ${profile.display_name}`}
    >
      {isPending ? (
        <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
      ) : (
        <>
          <UserPlus className="h-4 w-4 mr-1.5" aria-hidden="true" />
          Follow
        </>
      )}
    </Button>
  );
}