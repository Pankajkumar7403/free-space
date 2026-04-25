// 📍 LOCATION: free-space/frontend/apps/web/src/components/features/profile/ProfilePostsGrid.tsx
//
// ProfilePostsGrid — 3-column Instagram-style grid of a user's posts.
// Tapping a post opens the post detail modal (intercepted route).
// Shows like count + comment count overlay on hover.

'use client';

import Image from 'next/image';
import Link from 'next/link';
import { Heart, MessageCircle, Film } from 'lucide-react';

import { useUserPosts, flattenPostPages } from '@/hooks';
import type { Post } from '@qommunity/types';
import { formatCount } from '@/lib/utils';
import { Skeleton } from '@/components/ui/Skeleton';

interface ProfilePostsGridProps {
  username: string;
  isPrivate?: boolean;
}

export function ProfilePostsGrid({ username, isPrivate = false }: ProfilePostsGridProps) {
  const {
    data,
    isLoading,
    isError,
    isFetchingNextPage,
    hasNextPage,
    fetchNextPage,
    ref: sentinelRef,
  } = useUserPostsWithRef(username);

  const posts = flattenPostPages(data);

  if (isLoading) return <ProfilePostsGridSkeleton />;

  if (isPrivate) {
    return (
      <div className="flex items-center justify-center py-16">
        <p className="text-sm text-muted-foreground">
          Follow to see posts.
        </p>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex items-center justify-center py-16">
        <p className="text-sm text-muted-foreground">Could not load posts.</p>
      </div>
    );
  }

  if (posts.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 gap-3">
        <div className="h-12 w-12 rounded-full border-2 border-muted-foreground/30 flex items-center justify-center">
          <Film className="h-6 w-6 text-muted-foreground/50" aria-hidden="true" />
        </div>
        <p className="text-sm font-medium">No posts yet</p>
      </div>
    );
  }

  return (
    <div>
      <div
        className="grid grid-cols-3 gap-px bg-border"
        role="list"
        aria-label={`${username}'s posts`}
      >
        {posts.map((post) => (
          <PostGridItem key={post.id} post={post} />
        ))}
      </div>

      {/* Infinite scroll sentinel */}
      {hasNextPage && (
        <div
          ref={sentinelRef}
          className="h-4"
          aria-hidden="true"
        />
      )}
    </div>
  );
}

// ─── Grid cell ────────────────────────────────────────────────────────────────
function PostGridItem({ post }: { post: Post }) {
  const thumbnail =
    post.media[0]?.thumbnail_url ??
    post.media[0]?.processed_url ??
    post.media[0]?.original_url;

  const isVideo = post.media[0]?.file_type === 'video';

  return (
    <Link
      href={`/p/${post.id}`}
      className="relative aspect-square block bg-muted overflow-hidden group"
      role="listitem"
      aria-label={`Post with ${post.likes_count} likes and ${post.comments_count} comments`}
    >
      {thumbnail ? (
        <Image
          src={thumbnail}
          alt={post.content ?? 'Post image'}
          fill
          sizes="(max-width: 640px) 33vw, 220px"
          className="object-cover transition-transform duration-300 group-hover:scale-105"
        />
      ) : (
        // Text-only post fallback
        <div className="absolute inset-0 flex items-center justify-center p-3 bg-gradient-to-br from-primary/10 to-accent/10">
          <p className="text-xs text-center line-clamp-4 text-foreground/80">
            {post.content}
          </p>
        </div>
      )}

      {/* Video indicator */}
      {isVideo && (
        <Film
          className="absolute top-2 right-2 h-4 w-4 text-white drop-shadow-md"
          aria-hidden="true"
        />
      )}

      {/* Multi-image indicator */}
      {post.media.length > 1 && !isVideo && (
        <div
          className="absolute top-2 right-2 h-4 w-4 text-white drop-shadow-md"
          aria-hidden="true"
        >
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M2 6h2v14h14v2H2V6zm4-4h16v16H6V2zm2 2v12h12V4H8z" />
          </svg>
        </div>
      )}

      {/* Hover overlay with engagement stats */}
      <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex items-center justify-center gap-4">
        <span className="flex items-center gap-1.5 text-white font-semibold text-sm">
          <Heart className="h-4 w-4 fill-white" aria-hidden="true" />
          {formatCount(post.likes_count)}
        </span>
        {post.allow_comments && (
          <span className="flex items-center gap-1.5 text-white font-semibold text-sm">
            <MessageCircle className="h-4 w-4 fill-white" aria-hidden="true" />
            {formatCount(post.comments_count)}
          </span>
        )}
      </div>
    </Link>
  );
}

// ─── Infinite scroll with ref ─────────────────────────────────────────────────
// Wrapper that also returns a sentinel ref for IntersectionObserver
import { useEffect, useRef } from 'react';


function useUserPostsWithRef(username: string) {
  const query = useUserPosts(username);
  const sentinelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel || !query.hasNextPage || query.isFetchingNextPage) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) {
          void query.fetchNextPage();
        }
      },
      { rootMargin: '200px' },
    );

    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [query]);

  return { ...query, ref: sentinelRef };
}

// ─── Loading skeleton ─────────────────────────────────────────────────────────
function ProfilePostsGridSkeleton() {
  return (
    <div
      className="grid grid-cols-3 gap-px bg-border"
      aria-hidden="true"
    >
      {Array.from({ length: 9 }).map((_, i) => (
        <Skeleton key={i} className="aspect-square w-full rounded-none" />
      ))}
    </div>
  );
}