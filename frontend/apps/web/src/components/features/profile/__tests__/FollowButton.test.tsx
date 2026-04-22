// 📍 LOCATION: free-space/frontend/apps/web/src/components/features/profile/__tests__/FollowButton.test.tsx

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';

import { server } from '@/test/mswServer';
import { mockUser, mockUserSummary } from '@/test/factories';
import { renderWithAppProviders } from '@/test/renderWithAppProviders';
import { FollowButton } from '../FollowButton';
import type { User } from '@qommunity/types';

// Build a full User from UserSummary for test purposes
function makeUser(overrides: Partial<User> = {}): User {
  return {
    ...mockUser(),
    ...overrides,
  } as User;
}

vi.mock('@/stores/authStore', () => ({
  useAuthStore: (sel: (s: { user: ReturnType<typeof mockUser> }) => unknown) =>
    sel({ user: mockUser({ id: 'viewer-123', username: 'viewer' }) }),
}));

function renderWithQuery(ui: React.ReactElement) {
  return renderWithAppProviders(ui);
}

describe('FollowButton', () => {
  const user = userEvent.setup();

  it('renders Follow when not following', () => {
    const profile = makeUser({ is_following: false, follow_request_sent: false });
    renderWithQuery(<FollowButton user={profile} />);
    expect(screen.getByRole('button', { name: /follow/i })).toBeInTheDocument();
  });

  it('renders Following when already following', () => {
    const profile = makeUser({ is_following: true });
    renderWithQuery(<FollowButton user={profile} />);
    expect(screen.getByRole('button', { name: /following/i })).toBeInTheDocument();
  });

  it('renders Requested when follow request is pending', () => {
    const profile = makeUser({ is_following: false, follow_request_sent: true });
    renderWithQuery(<FollowButton user={profile} />);
    expect(screen.getByRole('button', { name: /requested/i })).toBeInTheDocument();
  });

  it('renders Edit profile for own profile', () => {
    const profile = makeUser({ username: 'viewer' }); // same as mocked currentUser
    renderWithQuery(<FollowButton user={profile} />);
    expect(screen.getByRole('button', { name: /edit profile/i })).toBeInTheDocument();
  });

  it('calls follow API on click and updates optimistically', async () => {
    const profile = makeUser({ is_following: false, follow_request_sent: false });
    renderWithQuery(<FollowButton user={profile} />);

    await user.click(screen.getByRole('button', { name: /follow/i }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /following/i })).toBeInTheDocument();
    });
  });

  it('shows Unfollow on hover when following', async () => {
    const profile = makeUser({ is_following: true });
    renderWithQuery(<FollowButton user={profile} />);

    const btn = screen.getByRole('button', { name: /following/i });
    await user.hover(btn);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /unfollow/i })).toBeInTheDocument();
    });
  });

  it('rolls back on API error', async () => {
    server.use(
      http.post('http://localhost:8000/api/v1/users/:username/follow/', () =>
        HttpResponse.json(
          { error_code: 'SERVER_ERROR', message: 'Failed', details: {} },
          { status: 500 },
        ),
      ),
    );

    const profile = makeUser({ is_following: false });
    renderWithQuery(<FollowButton user={profile} />);

    await user.click(screen.getByRole('button', { name: /follow/i }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /follow/i })).toBeInTheDocument();
    });
  });
});