// 📍 LOCATION: free-space/frontend/apps/web/src/lib/session.ts
//
// Web session helpers.
// The web app uses httpOnly cookies for the refresh token (set by /api/auth/set-cookie).
// The access token lives only in Zustand memory - never in localStorage.
// This file provides helpers called by AuthProvider and the login flow.

/**
 * Called after a successful login or register.
 * Sends the refresh token to the Next.js API route which sets it
 * as an httpOnly cookie (JavaScript can never read httpOnly cookies).
 */
export async function persistRefreshToken(refreshToken: string): Promise<void> {
  const res = await fetch('/api/auth/set-cookie', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ refresh: refreshToken }),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(text || `Failed to set session cookie (${res.status})`);
  }
}

/**
 * Called on logout.
 * Tells the Next.js API route to blacklist the token on the backend
 * and delete the httpOnly cookie.
 */
export async function destroySession(): Promise<void> {
  await fetch('/api/auth/logout', {
    method: 'POST',
    credentials: 'include',
  });
}

/**
 * Called by AuthProvider on mount to restore session from the httpOnly cookie.
 * The cookie is sent automatically by the browser - we never read it in JS.
 * Returns { user, access } on success, null on failure.
 */
export async function fetchSession(): Promise<{
  user: import('@qommunity/types').AuthenticatedUser;
  access: string;
} | null> {
  try {
    const res = await fetch('/api/auth/session', {
      credentials: 'include',
      cache: 'no-store',
    });
    if (!res.ok) return null;
    return res.json() as Promise<{
      user: import('@qommunity/types').AuthenticatedUser;
      access: string;
    }>;
  } catch {
    return null;
  }
}
