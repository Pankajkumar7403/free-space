import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { NextRequest } from 'next/server';

import { GET } from '@/app/api/auth/oauth/init/route';

describe('GET /api/auth/oauth/init', () => {
  let originalApiInternalUrl: string | undefined;
  const fetchMock = vi.fn<typeof fetch>();
  const redirectUri =
    'http://localhost:3000/api/auth/oauth/callback?provider=google';

  beforeEach(() => {
    originalApiInternalUrl = process.env.API_INTERNAL_URL;
    vi.stubGlobal('fetch', fetchMock);
    delete process.env.API_INTERNAL_URL;
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    fetchMock.mockReset();
    if (originalApiInternalUrl) {
      process.env.API_INTERNAL_URL = originalApiInternalUrl;
    } else {
      delete process.env.API_INTERNAL_URL;
    }
  });

  it('uses canonical 127.0.0.1 fallback when API_INTERNAL_URL is not set', async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          url: 'https://accounts.google.com/o/oauth2/v2/auth?client_id=demo',
        }),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        },
      ),
    );

    const request = new NextRequest(
      `http://localhost:3000/api/auth/oauth/init?provider=google&redirect_uri=${encodeURIComponent(redirectUri)}`,
    );

    const response = await GET(request);

    expect(response.status).toBe(200);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [target, options] = fetchMock.mock.calls[0] ?? [];
    const targetUrl = new URL(String(target));

    expect(targetUrl.origin).toBe('http://127.0.0.1:8000');
    expect(targetUrl.pathname).toBe('/api/v1/users/oauth/google/init/');
    expect(targetUrl.searchParams.get('redirect_uri')).toBe(redirectUri);
    expect(options).toMatchObject({
      method: 'GET',
      cache: 'no-store',
    });
    expect(options).not.toHaveProperty('body');
    expect(options).not.toHaveProperty('headers');
  });

  it('preserves provider and redirect_uri in upstream query params', async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ url: 'https://example.com/oauth' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    const request = new NextRequest(
      `http://localhost:3000/api/auth/oauth/init?provider=google&redirect_uri=${encodeURIComponent(redirectUri)}`,
    );

    await GET(request);

    const [target] = fetchMock.mock.calls[0] ?? [];
    const targetUrl = new URL(String(target));

    expect(targetUrl.searchParams.get('redirect_uri')).toBe(redirectUri);
  });
});
