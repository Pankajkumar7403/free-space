// 📍 LOCATION: free-space/frontend/apps/web/src/middleware.ts
//
// Next.js Edge Middleware — runs before every request.
// Protects routes by checking for the presence of the refresh token cookie.
// For true token validation, use the /api/auth/session API route (not edge-compatible with RS256).

import { type NextRequest, NextResponse } from 'next/server';

// ─── Route groups ─────────────────────────────────────────────────────────────

/** Routes that require authentication — redirect to /login if no cookie */
const PROTECTED_ROUTES = [
  '/feed',
  '/explore',
  '/notifications',
  '/settings',
  '/create',
];

/** Routes only for unauthenticated users — redirect to /feed if already authed */
const AUTH_ROUTES = ['/login', '/register', '/forgot-password', '/reset-password'];

/** Public routes — accessible regardless of auth state */
// (everything else, including /[username] profile pages)

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Read refresh token cookie (presence = likely authenticated)
  // Actual validity is checked by the AuthProvider on mount
  const hasSession = request.cookies.has('qommunity_refresh');

  // ── Redirect authenticated users away from auth pages ─────────────────────
  if (AUTH_ROUTES.some((route) => pathname.startsWith(route))) {
    if (hasSession) {
      return NextResponse.redirect(new URL('/feed', request.url));
    }
    return NextResponse.next();
  }

  // ── Redirect unauthenticated users away from protected pages ──────────────
  if (PROTECTED_ROUTES.some((route) => pathname.startsWith(route))) {
    if (!hasSession) {
      const loginUrl = new URL('/login', request.url);
      // Preserve the intended destination for post-login redirect
      loginUrl.searchParams.set('callbackUrl', pathname);
      return NextResponse.redirect(loginUrl);
    }
    return NextResponse.next();
  }

  return NextResponse.next();
}

export const config = {
  // Run on all routes except static assets, images, and favicon
  matcher: ['/((?!_next/static|_next/image|favicon|manifest|og-image|apple-touch|robots).*)'],
};
