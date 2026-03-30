// 📍 LOCATION: free-space/frontend/apps/web/src/app/api/auth/set-cookie/route.ts
//
// POST /api/auth/set-cookie
// Called client-side after a successful login/register.
// Sets the refresh token in an httpOnly cookie — inaccessible to JavaScript.
// This is the correct Web security pattern: access token in memory, refresh in httpOnly cookie.

import { type NextRequest, NextResponse } from 'next/server';

const COOKIE_NAME    = 'qommunity_refresh';
const COOKIE_MAX_AGE = 60 * 60 * 24 * 30; // 30 days — matches backend refresh token TTL

export async function POST(request: NextRequest) {
  try {
    const body = (await request.json()) as { refresh?: string };

    if (!body.refresh || typeof body.refresh !== 'string') {
      return NextResponse.json({ error: 'refresh token required' }, { status: 400 });
    }

    const response = NextResponse.json({ ok: true });

    response.cookies.set(COOKIE_NAME, body.refresh, {
      httpOnly: true,                              // JS cannot read this cookie
      secure: process.env.NODE_ENV === 'production',// HTTPS only in production
      sameSite: 'lax',                             // CSRF protection
      maxAge: COOKIE_MAX_AGE,
      path: '/',
    });

    return response;
  } catch {
    return NextResponse.json({ error: 'invalid request body' }, { status: 400 });
  }
}
