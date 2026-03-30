// 📍 LOCATION: free-space/frontend/apps/web/src/components/features/feed/PostCard.tsx
//
// PostCard — the single most-rendered component in the app.
// Every post in the feed is one PostCard.
//
// Responsibilities:
//   - Render author avatar, name, pronouns (outing-prevention-aware)
//   - Render post content with hashtag highlighting
//   - Render media grid (1, 2, 3, 4+ images/videos)
//   - Render action bar: like, comment, share, bookmark
//   - Handle like toggle with optimistic update
//   - Show visibility badge (public / followers / close friends / anonymous)
//   - Show post options dropdown (edit / delete / report)
//
// What it does NOT do:
//   - Fetch data (parent FeedList passes the post as a prop)
//   - Navigate (parent handles click routing)

'use client';

import React, { useState, useCallback } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { formatDistanceToNowStrict } from 'date-fns';
import {
  Heart, MessageCircle, Share2, Bookmark,
  MoreHorizontal, Globe, Users, Lock, UserX,
  CheckCircle2,
} from 'lucide-react';

import type { Post } from '@qommunity/types';
import { useLikePost } from '@qommunity/hooks';

import { cn } from '@/lib/utils';
import { formatCount } from '@/lib/utils';
import { Avatar } from '@/components/ui/Avatar';
import { Button } from '@/components/ui/Button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/DropdownMenu';
import { useAuthStore } from '@/stores/authStore';
import { useToast } from '@/components/ui/Toast';

// ─── Props ────────────────────────────────────────────────────────────────────
interface PostCardProps {
  post: Post;
  /** Whether this is rendered inside a modal (affects navigation behavior) */
  isModal?: boolean;
  /** Called when comment button is clicked */
  onCommentClick?: (postId: string) => void;
}

// ─── Visibility badge config ──────────────────────────────────────────────────
const VISIBILITY_CONFIG = {
  public:        { icon: Globe,  label: 'Public',       className: 'text-green-600 dark:text-green-400'  },
  followers_only:{ icon: Users,  label: 'Followers',    className: 'text-blue-600 dark:text-blue-400'    },
  close_friends: { icon: Users,  label: 'Close friends',className: 'text-purple-600 dark:text-purple-400'},
  private:       { icon: Lock,   label: 'Private',      className: 'text-gray-500'                       },
  anonymous:     { icon: UserX,  label: 'Anonymous',    className: 'text-orange-600 dark:text-orange-400'},
} as const;

// ─── Component ────────────────────────────────────────────────────────────────
export function PostCard({ post, isModal = false, onCommentClick }: PostCardProps) {
  const router        = useRouter();
  const currentUser   = useAuthStore((s) => s.user);
  const { toast }     = useToast();
  const likePost      = useLikePost();

  const isOwnPost     = currentUser?.id === post.author.id;
  const isFollowing   = post.author.is_following ?? false;

  // ── Outing prevention: only show pronouns per visibility setting ───────────
  const showPronouns =
    post.author.pronouns !== null &&
    (post.author.pronouns_visibility === 'public' ||
      (post.author.pronouns_visibility === 'followers_only' && isFollowing));

  // ── Relative timestamp ─────────────────────────────────────────────────────
  const timeAgo = formatDistanceToNowStrict(new Date(post.created_at), {
    addSuffix: false,
  });

  // ── Like handler ───────────────────────────────────────────────────────────
  const handleLike = useCallback(() => {
    likePost.mutate(
      { postId: post.id, isLiked: post.is_liked },
      {
        onError: () => {
          toast({ title: 'Failed to update like', variant: 'error' });
        },
      },
    );
  }, [likePost, post.id, post.is_liked, toast]);

  // ── Share handler ──────────────────────────────────────────────────────────
  const handleShare = useCallback(async () => {
    const url = `${window.location.origin}/p/${post.id}`;
    try {
      if (navigator.share) {
        await navigator.share({ url, title: 'Check this out on Qommunity' });
      } else {
        await navigator.clipboard.writeText(url);
        toast({ title: 'Link copied!', variant: 'success' });
      }
    } catch {
      // User cancelled share dialog — not an error
    }
  }, [post.id, toast]);

  // ── Navigate to post detail ────────────────────────────────────────────────
  const handlePostClick = useCallback(() => {
    if (!isModal) {
      router.push(`/p/${post.id}`);
    }
  }, [isModal, post.id, router]);

  const VisibilityIcon = post.is_anonymous
    ? VISIBILITY_CONFIG.anonymous.icon
    : VISIBILITY_CONFIG[post.visibility].icon;

  const visibilityClass = post.is_anonymous
    ? VISIBILITY_CONFIG.anonymous.className
    : VISIBILITY_CONFIG[post.visibility].className;

  return (
    <article
      className="border-b border-border bg-background py-4 px-0 sm:px-4 sm:rounded-xl sm:border sm:mb-3"
      aria-label={`Post by ${post.is_anonymous ? 'Anonymous' : post.author.display_name}`}
    >
      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div className="flex items-start justify-between px-4 sm:px-0 mb-3">
        <div className="flex items-center gap-3">
          {/* Avatar — links to profile unless anonymous */}
          {post.is_anonymous ? (
            <div className="h-10 w-10 rounded-full bg-muted flex items-center justify-center flex-shrink-0">
              <UserX className="h-5 w-5 text-muted-foreground" aria-hidden="true" />
            </div>
          ) : (
            <Link
              href={`/${post.author.username}`}
              aria-label={`View ${post.author.display_name}'s profile`}
            >
              <Avatar
                src={post.author.avatar_url}
                alt={post.author.display_name}
                size="md"
              />
            </Link>
          )}

          {/* Author info */}
          <div className="min-w-0">
            <div className="flex items-center gap-1.5 flex-wrap">
              {post.is_anonymous ? (
                <span className="text-sm font-semibold text-muted-foreground">Anonymous</span>
              ) : (
                <Link
                  href={`/${post.author.username}`}
                  className="text-sm font-semibold hover:underline underline-offset-2"
                >
                  {post.author.display_name}
                </Link>
              )}
              {!post.is_anonymous && post.author.is_verified && (
                <CheckCircle2
                  className="h-3.5 w-3.5 text-primary flex-shrink-0"
                  aria-label="Verified account"
                />
              )}
              {showPronouns && (
                <span
                  className="text-xs text-muted-foreground"
                  aria-label={`Pronouns: ${post.author.pronouns}`}
                >
                  {post.author.pronouns}
                </span>
              )}
            </div>
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              {!post.is_anonymous && (
                <>
                  <span>@{post.author.username}</span>
                  <span aria-hidden="true">·</span>
                </>
              )}
              <time dateTime={post.created_at}>{timeAgo}</time>
              {post.visibility !== 'public' && (
                <>
                  <span aria-hidden="true">·</span>
                  <VisibilityIcon
                    className={cn('h-3 w-3', visibilityClass)}
                    aria-label={`Visible to: ${VISIBILITY_CONFIG[post.visibility].label}`}
                  />
                </>
              )}
            </div>
          </div>
        </div>

        {/* Post options dropdown */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon-sm"
              aria-label="Post options"
              className="text-muted-foreground -mr-1"
            >
              <MoreHorizontal className="h-5 w-5" aria-hidden="true" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            {isOwnPost ? (
              <>
                <DropdownMenuItem onSelect={() => router.push(`/p/${post.id}/edit`)}>
                  Edit post
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem destructive onSelect={() => { /* handled in Sprint 5 */ }}>
                  Delete post
                </DropdownMenuItem>
              </>
            ) : (
              <>
                <DropdownMenuItem onSelect={handleShare}>
                  Copy link
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem destructive onSelect={() => { /* report flow Sprint 7 */ }}>
                  Report post
                </DropdownMenuItem>
              </>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* ── Content ────────────────────────────────────────────────────────── */}
      {post.content && (
        <div className="px-4 sm:px-0 mb-3">
          <PostContent content={post.content} postId={post.id} />
        </div>
      )}

      {/* ── Media grid ─────────────────────────────────────────────────────── */}
      {post.media.length > 0 && (
        <button
          className="w-full mb-3 cursor-pointer"
          onClick={handlePostClick}
          aria-label="View post"
        >
          <MediaGrid media={post.media} />
        </button>
      )}

      {/* ── Action bar ─────────────────────────────────────────────────────── */}
      <div className="flex items-center gap-1 px-4 sm:px-0">
        {/* Like button */}
        <button
          onClick={handleLike}
          disabled={likePost.isPending}
          className={cn(
            'flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-sm transition-all',
            'hover:bg-red-50 dark:hover:bg-red-950/20 group',
            'disabled:opacity-60 disabled:pointer-events-none',
            post.is_liked
              ? 'text-red-500'
              : 'text-muted-foreground hover:text-red-500',
          )}
          aria-label={post.is_liked ? 'Unlike post' : 'Like post'}
          aria-pressed={post.is_liked}
        >
          <Heart
            className={cn(
              'h-5 w-5 transition-all duration-200',
              post.is_liked && 'fill-current animate-heart-pop',
            )}
            aria-hidden="true"
          />
          {post.likes_count > 0 && (
            <span className="text-xs font-medium tabular-nums">
              {formatCount(post.likes_count)}
            </span>
          )}
        </button>

        {/* Comment button */}
        {post.allow_comments && (
          <button
            onClick={() => onCommentClick?.(post.id)}
            className="flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-sm text-muted-foreground hover:text-foreground hover:bg-muted transition-all"
            aria-label={`${post.comments_count} comments`}
          >
            <MessageCircle className="h-5 w-5" aria-hidden="true" />
            {post.comments_count > 0 && (
              <span className="text-xs font-medium tabular-nums">
                {formatCount(post.comments_count)}
              </span>
            )}
          </button>
        )}

        {/* Share button */}
        <button
          onClick={handleShare}
          className="flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-sm text-muted-foreground hover:text-foreground hover:bg-muted transition-all"
          aria-label="Share post"
        >
          <Share2 className="h-5 w-5" aria-hidden="true" />
        </button>

        {/* Spacer */}
        <div className="flex-1" aria-hidden="true" />

        {/* Bookmark button */}
        <button
          className={cn(
            'flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-sm transition-all',
            'hover:bg-muted',
            post.is_bookmarked
              ? 'text-primary'
              : 'text-muted-foreground hover:text-foreground',
          )}
          aria-label={post.is_bookmarked ? 'Remove bookmark' : 'Bookmark post'}
          aria-pressed={post.is_bookmarked}
        >
          <Bookmark
            className={cn('h-5 w-5', post.is_bookmarked && 'fill-current')}
            aria-hidden="true"
          />
        </button>
      </div>
    </article>
  );
}

// ─── PostContent: renders text with clickable #hashtags and @mentions ─────────
function PostContent({ content, postId }: { content: string; postId: string }) {
  const [expanded, setExpanded] = useState(false);
  const TRUNCATE_AT = 300;
  const shouldTruncate = content.length > TRUNCATE_AT && !expanded;
  const displayContent = shouldTruncate
    ? content.slice(0, TRUNCATE_AT)
    : content;

  // Split content into text + hashtag/mention tokens
  const tokens = displayContent.split(/(#[a-zA-Z0-9_]+|@[a-zA-Z0-9_]+)/g);

  return (
    <p className="text-sm leading-relaxed break-words">
      {tokens.map((token, i) => {
        if (token.startsWith('#')) {
          return (
            <Link
              key={i}
              href={`/hashtag/${token.slice(1)}`}
              className="text-primary font-medium hover:underline"
            >
              {token}
            </Link>
          );
        }
        if (token.startsWith('@')) {
          return (
            <Link
              key={i}
              href={`/${token.slice(1)}`}
              className="text-primary font-medium hover:underline"
            >
              {token}
            </Link>
          );
        }
        return <span key={i}>{token}</span>;
      })}
      {shouldTruncate && (
        <>
          {'... '}
          <button
            onClick={() => setExpanded(true)}
            className="text-muted-foreground hover:text-foreground text-sm font-medium"
          >
            more
          </button>
        </>
      )}
    </p>
  );
}

// ─── MediaGrid: 1, 2, 3, or 4+ images with Instagram-style layout ─────────────
function MediaGrid({ media }: { media: Post['media'] }) {
  const count = Math.min(media.length, 4);
  const hasMore = media.length > 4;

  if (count === 1) {
    const item = media[0]!;
    return (
      <div className="relative w-full aspect-square sm:aspect-[4/3] overflow-hidden sm:rounded-xl bg-muted">
        <MediaItem item={item} fill />
      </div>
    );
  }

  if (count === 2) {
    return (
      <div className="grid grid-cols-2 gap-0.5 sm:rounded-xl overflow-hidden">
        {media.slice(0, 2).map((item, i) => (
          <div key={item.id} className="relative aspect-square bg-muted">
            <MediaItem item={item} fill />
          </div>
        ))}
      </div>
    );
  }

  if (count === 3) {
    return (
      <div className="grid grid-cols-2 gap-0.5 sm:rounded-xl overflow-hidden">
        <div className="relative aspect-square row-span-2 bg-muted">
          <MediaItem item={media[0]!} fill />
        </div>
        {media.slice(1, 3).map((item) => (
          <div key={item.id} className="relative aspect-square bg-muted">
            <MediaItem item={item} fill />
          </div>
        ))}
      </div>
    );
  }

  // 4+ images
  return (
    <div className="grid grid-cols-2 gap-0.5 sm:rounded-xl overflow-hidden">
      {media.slice(0, 4).map((item, i) => (
        <div key={item.id} className="relative aspect-square bg-muted">
          <MediaItem item={item} fill />
          {i === 3 && hasMore && (
            <div className="absolute inset-0 bg-black/60 flex items-center justify-center">
              <span className="text-white text-xl font-bold">
                +{media.length - 4}
              </span>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

// ─── Single media item (image or video) ───────────────────────────────────────
function MediaItem({
  item,
  fill = false,
}: {
  item: Post['media'][number];
  fill?: boolean;
}) {
  const src = item.processed_url ?? item.original_url;

  if (item.file_type === 'video') {
    return (
      <video
        src={src}
        poster={item.thumbnail_url ?? undefined}
        className={fill ? 'absolute inset-0 w-full h-full object-cover' : 'w-full'}
        muted
        playsInline
        preload="metadata"
        aria-label="Video post"
      />
    );
  }

  return (
    <Image
      src={src}
      alt="Post image"
      fill={fill}
      sizes="(max-width: 640px) 100vw, 470px"
      className="object-cover"
      placeholder="blur"
      blurDataURL="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjQwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZTVlN2ViIi8+PC9zdmc+"
    />
  );
}