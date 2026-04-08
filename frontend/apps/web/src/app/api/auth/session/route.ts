// 📍 LOCATION: free-space/frontend/apps/web/src/app/api/auth/session/route.ts
//
// GET /api/auth/session
// Called by AuthProvider on mount to restore session from the httpOnly refresh cookie.
// Uses the refresh token to get a new access token + current user profile.
// Returns: { user: AuthenticatedUser, access: string }

import { type NextRequest, NextResponse } from 'next/server';
import type { AuthenticatedUser } from '@qommunity/types';

const COOKIE_NAME   = 'qommunity_refresh';
const API_INTERNAL  = process.env.API_INTERNAL_URL ?? 'http://localhost:8000/api/v1';

interface RefreshResponse {
  access: string;
}

export async function GET(request: NextRequest) {
  const refreshToken = request.cookies.get(COOKIE_NAME)?.value;

  if (!refreshToken) {
    return NextResponse.json({ error: 'no session' }, { status: 401 });
  }

  try {
    // Step 1: Exchange refresh token for new access token
    const refreshRes = await fetch(`${API_INTERNAL}/users/token/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: refreshToken }),
      // Next.js cache: no-store — always fresh
      cache: 'no-store',
    });

    if (!refreshRes.ok) {
      // Refresh token is expired or blacklisted — clear the cookie
      const response = NextResponse.json({ error: 'session expired' }, { status: 401 });
      response.cookies.delete(COOKIE_NAME);
      return response;
    }

    const { access } = (await refreshRes.json()) as RefreshResponse;

    // Step 2: Fetch current user with the new access token
    const meRes = await fetch(`${API_INTERNAL}/users/me/`, {
      headers: { Authorization: `Bearer ${access}` },
      cache: 'no-store',
    });

    if (!meRes.ok) {
      const response = NextResponse.json({ error: 'user fetch failed' }, { status: 401 });
      response.cookies.delete(COOKIE_NAME);
      return response;
    }

    const user = (await meRes.json()) as AuthenticatedUser;

    return NextResponse.json({ user, access });
  } catch {
    return NextResponse.json({ error: 'session restore failed' }, { status: 500 });
  }
}
