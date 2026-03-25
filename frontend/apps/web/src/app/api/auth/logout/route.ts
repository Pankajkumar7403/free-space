// 📍 LOCATION: free-space/frontend/apps/web/src/app/api/auth/logout/route.ts
//
// POST /api/auth/logout
// Blacklists the refresh token on the backend, then clears the httpOnly cookie.

import { type NextRequest, NextResponse } from 'next/server';

const COOKIE_NAME  = 'qommunity_refresh';
const API_INTERNAL = process.env.API_INTERNAL_URL ?? 'http://localhost:8000/api/v1';

export async function POST(request: NextRequest) {
  const refreshToken = request.cookies.get(COOKIE_NAME)?.value;

  // Best-effort: call backend logout even if we don't have the token
  if (refreshToken) {
    try {
      await fetch(`${API_INTERNAL}/users/auth/logout/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh: refreshToken }),
        cache: 'no-store',
      });
    } catch {
      // Swallow error — we always clear the cookie regardless
    }
  }

  const response = NextResponse.json({ ok: true });
  response.cookies.delete(COOKIE_NAME);
  return response;
}
