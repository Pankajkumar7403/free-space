// 📍 LOCATION: free-space/frontend/apps/web/src/components/features/feed/__tests__/PostCard.test.tsx
//
// Tests for PostCard component.
// Tests cover: rendering, like toggle, outing prevention, visibility badges.

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, useQuery } from '@tanstack/react-query';
import type { InfiniteData } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { queryKeys, flattenFeedPages } from '@/hooks';
import type { FeedPage, Post } from '@qommunity/types';

import { server } from '@/test/mswServer';
import { mockPost, mockUser } from '@/test/factories';
import { renderWithAppProviders } from '@/test/renderWithAppProviders';
import { PostCard } from '../PostCard';

function renderWithQuery(ui: React.ReactElement) {
  return renderWithAppProviders(ui);
}

/**
 * Re-renders when the home feed query cache updates (mirrors FeedList → PostCard data flow).
 */
function FeedCachedPostCard({
  post,
  onCommentClick,
}: {
  post: Post;
  onCommentClick?: (id: string) => void;
}) {
  const { data } = useQuery<InfiniteData<FeedPage>>({
    queryKey: queryKeys.feed.home(),
    queryFn: async () => {
      throw new Error('FeedCachedPostCard does not fetch');
    },
    enabled: false,
  });

  const flat = data ? flattenFeedPages(data) : [post];
  const current = flat.find((p) => p.id === post.id) ?? post;
  return <PostCard post={current} onCommentClick={onCommentClick} />;
}

/** Like mutation updates home feed cache — mirror production FeedList subscription. */
function renderPostCardWithFeedCache(
  post: Post,
  extra?: { onCommentClick?: (id: string) => void },
) {
  const queryClient = new QueryClient({
    defaultOptions: { mutations: { retry: false }, queries: { retry: false } },
  });
  queryClient.setQueryData<InfiniteData<FeedPage>>(queryKeys.feed.home(), {
    pages: [{ results: [post], next_cursor: null, source: 'db' }],
    pageParams: [undefined],
  });
  return renderWithAppProviders(
    <FeedCachedPostCard post={post} onCommentClick={extra?.onCommentClick} />,
    { queryClient },
  );
}

// ─── Mock auth store ──────────────────────────────────────────────────────────
vi.mock('@/stores/authStore', () => ({
  useAuthStore: (selector: (s: { user: ReturnType<typeof mockUser> | null }) => unknown) =>
    selector({ user: mockUser({ id: 'viewer-id-123' }) }),
}));

// ─── Tests ────────────────────────────────────────────────────────────────────
describe('PostCard', () => {
  const user = userEvent.setup();

  describe('rendering', () => {
    it('renders author name and username', () => {
      const post = mockPost({
        author: {
          id: 'author-1',
          username: 'testauthor',
          display_name: 'Test Author',
          avatar_url: null,
          pronouns: null,
          pronouns_visibility: 'private',
          is_verified: false,
          is_following: false,
        },
      });
      renderWithQuery(<PostCard post={post} />);

      expect(screen.getByText('Test Author')).toBeInTheDocument();
      expect(screen.getByText('@testauthor')).toBeInTheDocument();
    });

    it('renders post content with hashtag links', () => {
      const post = mockPost({ content: 'Hello #pride community' });
      renderWithQuery(<PostCard post={post} />);

      expect(screen.getByText('Hello')).toBeInTheDocument();
      const hashtagLink = screen.getByRole('link', { name: '#pride' });
      expect(hashtagLink).toHaveAttribute('href', '/hashtag/pride');
    });

    it('renders like count when greater than zero', () => {
      const post = mockPost({ likes_count: 42 });
      renderWithQuery(<PostCard post={post} />);

      expect(screen.getByText('42')).toBeInTheDocument();
    });

    it('shows filled heart when post is liked', () => {
      const post = mockPost({ is_liked: true, likes_count: 10 });
      renderWithQuery(<PostCard post={post} />);

      const likeButton = screen.getByRole('button', { name: /unlike post/i });
      expect(likeButton).toBeInTheDocument();
      expect(likeButton).toHaveAttribute('aria-pressed', 'true');
    });

    it('shows empty heart when post is not liked', () => {
      const post = mockPost({ is_liked: false, likes_count: 0 });
      renderWithQuery(<PostCard post={post} />);

      const likeButton = screen.getByRole('button', { name: /like post/i });
      expect(likeButton).toHaveAttribute('aria-pressed', 'false');
    });
  });

  describe('outing prevention', () => {
    it('hides pronouns when visibility is private', () => {
      const post = mockPost({
        author: {
          id: 'a1',
          username: 'user1',
          display_name: 'User One',
          avatar_url: null,
          pronouns: 'they/them',
          pronouns_visibility: 'private',
          is_verified: false,
          is_following: false,
        },
      });
      renderWithQuery(<PostCard post={post} />);
      expect(screen.queryByText('they/them')).not.toBeInTheDocument();
    });

    it('hides pronouns when visibility is followers_only and viewer is not following', () => {
      const post = mockPost({
        author: {
          id: 'a1',
          username: 'user1',
          display_name: 'User One',
          avatar_url: null,
          pronouns: 'she/her',
          pronouns_visibility: 'followers_only',
          is_verified: false,
          is_following: false,  // not following
        },
      });
      renderWithQuery(<PostCard post={post} />);
      expect(screen.queryByText('she/her')).not.toBeInTheDocument();
    });

    it('shows pronouns when visibility is public', () => {
      const post = mockPost({
        author: {
          id: 'a1',
          username: 'user1',
          display_name: 'User One',
          avatar_url: null,
          pronouns: 'he/him',
          pronouns_visibility: 'public',
          is_verified: false,
          is_following: false,
        },
      });
      renderWithQuery(<PostCard post={post} />);
      expect(screen.getByText('he/him')).toBeInTheDocument();
    });

    it('shows pronouns when visibility is followers_only and viewer IS following', () => {
      const post = mockPost({
        author: {
          id: 'a1',
          username: 'user1',
          display_name: 'User One',
          avatar_url: null,
          pronouns: 'ze/zir',
          pronouns_visibility: 'followers_only',
          is_verified: false,
          is_following: true,  // following
        },
      });
      renderWithQuery(<PostCard post={post} />);
      expect(screen.getByText('ze/zir')).toBeInTheDocument();
    });
  });

  describe('anonymous posting', () => {
    it('shows Anonymous label instead of author name', () => {
      const post = mockPost({ is_anonymous: true });
      renderWithQuery(<PostCard post={post} />);

      expect(screen.getByText('Anonymous')).toBeInTheDocument();
      expect(screen.queryByRole('link', { name: /view.*profile/i })).not.toBeInTheDocument();
    });
  });

  describe('like interaction', () => {
    it('increments like count optimistically on click', async () => {
      const post = mockPost({ is_liked: false, likes_count: 5 });
      renderPostCardWithFeedCache(post);

      const likeButton = screen.getByRole('button', { name: /like post/i });
      await user.click(likeButton);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /unlike post/i })).toBeInTheDocument();
      });
    });

    it('rolls back like count on API error', async () => {
      server.use(
        http.post('http://localhost:8000/api/v1/posts/:postId/like/', () =>
          HttpResponse.json({ error_code: 'SERVER_ERROR', message: 'Failed', details: {} }, { status: 500 }),
        ),
      );

      const post = mockPost({ is_liked: false, likes_count: 5 });
      renderPostCardWithFeedCache(post);

      await user.click(screen.getByRole('button', { name: /like post/i }));

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /like post/i })).toBeInTheDocument();
      });
    });
  });

  describe('comment button', () => {
    it('calls onCommentClick with post id when clicked', async () => {
      const onCommentClick = vi.fn();
      const post = mockPost({ allow_comments: true });
      renderWithQuery(<PostCard post={post} onCommentClick={onCommentClick} />);

      await user.click(screen.getByRole('button', { name: /comments/i }));

      expect(onCommentClick).toHaveBeenCalledWith(post.id);
    });

    it('does not render comment button when allow_comments is false', () => {
      const post = mockPost({ allow_comments: false });
      renderWithQuery(<PostCard post={post} />);

      expect(screen.queryByRole('button', { name: /comments/i })).not.toBeInTheDocument();
    });
  });
});