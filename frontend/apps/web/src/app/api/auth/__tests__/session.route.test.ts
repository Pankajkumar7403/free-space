import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { NextRequest } from 'next/server';

import { GET } from '@/app/api/auth/session/route';

describe('GET /api/auth/session', () => {
  let originalApiInternalUrl: string | undefined;
  const fetchMock = vi.fn<typeof fetch>();

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

  it('calls refresh and me on canonical fallback backend URL', async () => {
    fetchMock
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ access: 'access-token' }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ id: 'u1', username: 'demo' }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      );

    const request = new NextRequest('http://localhost:3000/api/auth/session', {
      headers: {
        cookie: 'qommunity_refresh=refresh-token',
      },
    });

    const response = await GET(request);
    const json = await response.json();

    expect(response.status).toBe(200);
    expect(json).toMatchObject({
      access: 'access-token',
      user: { id: 'u1', username: 'demo' },
    });
    expect(fetchMock).toHaveBeenCalledTimes(2);

    const [refreshTarget, refreshOptions] = fetchMock.mock.calls[0] ?? [];
    const refreshUrl = new URL(String(refreshTarget));
    expect(refreshUrl.origin).toBe('http://127.0.0.1:8000');
    expect(refreshUrl.pathname).toBe('/api/v1/users/token/refresh/');
    expect(refreshUrl.search).toBe('');
    expect(refreshOptions).toMatchObject({
      method: 'POST',
      cache: 'no-store',
      headers: { 'Content-Type': 'application/json' },
    });
    expect(JSON.parse(String(refreshOptions?.body))).toEqual({
      refresh: 'refresh-token',
    });

    const [meTarget, meOptions] = fetchMock.mock.calls[1] ?? [];
    const meUrl = new URL(String(meTarget));
    expect(meUrl.origin).toBe('http://127.0.0.1:8000');
    expect(meUrl.pathname).toBe('/api/v1/users/me/');
    expect(meUrl.search).toBe('');
    expect(meOptions).toMatchObject({
      cache: 'no-store',
      headers: { Authorization: 'Bearer access-token' },
    });
    expect(meOptions?.body).toBeUndefined();
  });
});
