import { type NextRequest, NextResponse } from 'next/server';

const API_INTERNAL = process.env.API_INTERNAL_URL ?? 'http://127.0.0.1:8000/api/v1';
const COOKIE_NAME = 'qommunity_refresh';
const COOKIE_MAX_AGE = 60 * 60 * 24 * 30;

export async function GET(request: NextRequest): Promise<NextResponse> {
  const provider = request.nextUrl.searchParams.get('provider');
  const code = request.nextUrl.searchParams.get('code');
  const state = request.nextUrl.searchParams.get('state');
  const callbackUrl = request.nextUrl.searchParams.get('callbackUrl');

  if (!provider || !code || !state) {
    return NextResponse.redirect(new URL('/login?error=oauth_missing_params', request.url));
  }

  // Must exactly match the redirect_uri used during OAuth init.
  const redirectUri = `${request.nextUrl.origin}/api/auth/oauth/callback?provider=${encodeURIComponent(provider)}`;
  const safeCallbackUrl = getSafeCallbackUrl(callbackUrl, request.nextUrl.origin);

  try {
    const oauthRes = await fetch(`${API_INTERNAL}/users/oauth/${encodeURIComponent(provider)}/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code, redirect_uri: redirectUri, state }),
      cache: 'no-store',
    });

    if (!oauthRes.ok) {
      return NextResponse.redirect(new URL('/login?error=oauth_failed', request.url));
    }

    const payload = (await oauthRes.json()) as { tokens?: { refresh?: string } };
    const refreshToken = payload.tokens?.refresh;
    if (!refreshToken) {
      return NextResponse.redirect(new URL('/login?error=oauth_failed', request.url));
    }

    const response = NextResponse.redirect(safeCallbackUrl);
    response.cookies.set(COOKIE_NAME, refreshToken, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: COOKIE_MAX_AGE,
      path: '/',
    });
    return response;
  } catch {
    return NextResponse.redirect(new URL('/login?error=oauth_failed', request.url));
  }
}

function getSafeCallbackUrl(callbackUrl: string | null, origin: string): URL {
  const fallback = new URL('/feed', origin);
  if (!callbackUrl) return fallback;

  try {
    const parsed = new URL(callbackUrl, origin);
    if (parsed.origin !== origin || !parsed.pathname.startsWith('/')) {
      return fallback;
    }
    return parsed;
  } catch {
    return fallback;
  }
}
