// 📍 LOCATION: free-space/frontend/apps/web/src/test/factories.ts
//
// Factory functions for all mock data used in tests.
// Never hardcode fixture JSON in test files — always use these.
// Pattern mirrors backend's factory_boy discipline.

import type { AuthenticatedUser, User, Post, Comment, Notification, TokenPair } from '@qommunity/types';

let _idCounter = 1;
const nextId = () => `test-uuid-${String(_idCounter++).padStart(4, '0')}`;
const now = () => new Date().toISOString();

// ─── User factories ───────────────────────────────────────────────────────────
export function mockUserSummary(overrides: Partial<User> = {}): User {
  return {
    id:                          nextId(),
    username:                    'testuser',
    email:                       'test@example.com',
    display_name:                'Test User',
    bio:                         'A test bio',
    avatar_url:                  null,
    website:                     null,
    pronouns:                    'they/them',
    pronouns_visibility:         'followers_only',
    gender_identity:             null,
    gender_identity_visibility:  'private',
    sexual_orientation:          null,
    sexual_orientation_visibility:'private',
    account_privacy:             'public',
    is_verified:                 false,
    is_active:                   true,
    followers_count:             0,
    following_count:             0,
    posts_count:                 0,
    is_following:                false,
    is_followed_by:              false,
    is_blocked:                  false,
    is_muted:                    false,
    follow_request_sent:         false,
    created_at:                  now(),
    updated_at:                  now(),
    ...overrides,
  };
}

export function mockUser(overrides: Partial<AuthenticatedUser> = {}): AuthenticatedUser {
  return {
    ...mockUserSummary(),
    email:            'test@example.com',
    email_verified:   true,
    notification_preferences: {
      likes_in_app:    true,
      likes_push:      true,
      comments_in_app: true,
      comments_push:   true,
      follows_in_app:  true,
      follows_push:    true,
      mentions_in_app: true,
      mentions_push:   true,
    },
    ...overrides,
  };
}

// ─── Token factories ──────────────────────────────────────────────────────────
export function mockTokens(overrides: Partial<TokenPair> = {}): TokenPair {
  return {
    access:  'mock-access-token-abc123',
    refresh: 'mock-refresh-token-xyz789',
    ...overrides,
  };
}

// ─── Post factories ───────────────────────────────────────────────────────────
export function mockPost(overrides: Partial<Post> = {}): Post {
  return {
    id:             nextId(),
    author:         mockUserSummary(),
    content:        'This is a test post content #test',
    media:          [],
    hashtags:       [{ id: nextId(), name: 'test', post_count: 1, trending_score: 0 }],
    visibility:     'public',
    is_anonymous:   false,
    allow_comments: true,
    location:       null,
    likes_count:    0,
    comments_count: 0,
    is_liked:       false,
    is_bookmarked:  false,
    created_at:     now(),
    updated_at:     now(),
    edited_at:      null,
    ...overrides,
  };
}

// ─── Comment factories ────────────────────────────────────────────────────────
export function mockComment(overrides: Partial<Comment> = {}): Comment {
  const postId = nextId();
  return {
    id:             nextId(),
    post_id:        postId,
    author:         mockUserSummary(),
    content:        'Test comment content',
    parent_id:      null,
    depth:          0,
    is_pinned:      false,
    likes_count:    0,
    replies_count:  0,
    is_liked:       false,
    is_hidden:      false,
    is_deleted:     false,
    created_at:     now(),
    updated_at:     now(),
    ...overrides,
  };
}
