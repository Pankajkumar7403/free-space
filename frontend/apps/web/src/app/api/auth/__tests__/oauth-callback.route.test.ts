import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { NextRequest } from 'next/server';

import { GET } from '@/app/api/auth/oauth/callback/route';

describe('GET /api/auth/oauth/callback', () => {
  const fetchMock = vi.fn<typeof fetch>();

  beforeEach(() => {
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    fetchMock.mockReset();
  });

  it('redirects with oauth_missing_params when state is missing', async () => {
    const request = new NextRequest(
      'http://localhost:3000/api/auth/oauth/callback?provider=google&code=abc',
    );

    const response = await GET(request);

    expect(response.status).toBe(307);
    expect(response.headers.get('location')).toBe(
      'http://localhost:3000/login?error=oauth_missing_params',
    );
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('sanitizes callbackUrl to prevent external redirect targets', async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ tokens: { refresh: 'refresh-token' } }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    const request = new NextRequest(
      'http://localhost:3000/api/auth/oauth/callback?provider=google&code=abc&state=signed&callbackUrl=https%3A%2F%2Fevil.example%2Fsteal',
    );

    const response = await GET(request);

    expect(response.status).toBe(307);
    expect(response.headers.get('location')).toBe('http://localhost:3000/feed');
  });
});
