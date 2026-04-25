//  LOCATION: free-space/frontend/apps/web/src/components/providers/AuthProvider.tsx
//
// Restores auth session on every page load from the httpOnly refresh cookie.
// Shows FullScreenLoader while loading to prevent a flash of the login page
// for users who are already authenticated.

'use client';

import { useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/authStore';
import { fetchSession } from '@/lib/session';
import { FullScreenLoader } from '@/components/ui/FullScreenLoader';

const PROTECTED_ROUTES = ['/feed', '/explore', '/hashtag', '/bookmarks', '/notifications', '/settings', '/create'];
const AUTH_ROUTES = ['/login', '/register', '/forgot-password', '/reset-password'];

interface AuthProviderProps {
  children: React.ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps): JSX.Element {
  const router = useRouter();
  const pathname = usePathname();
  const setAuth    = useAuthStore((s) => s.setAuth);
  const clearAuth  = useAuthStore((s) => s.clearAuth);
  const isLoading  = useAuthStore((s) => s.isLoading);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  useEffect(() => {
    let cancelled = false;

    async function restoreSession() {
      const session = await fetchSession();
      if (cancelled) return;

      if (session) {
        setAuth(session.user, session.access);
      } else {
        clearAuth();
      }
    }

    void restoreSession();

    return () => {
      cancelled = true;
    };
  }, [setAuth, clearAuth]);

  useEffect(() => {
    if (isLoading) return;

    const isProtected = PROTECTED_ROUTES.some((route) => pathname.startsWith(route));
    const isAuthRoute = AUTH_ROUTES.some((route) => pathname.startsWith(route));

    if (!isAuthenticated && isProtected) {
      const encoded = encodeURIComponent(pathname);
      router.replace(`/login?callbackUrl=${encoded}`);
      return;
    }
    if (isAuthenticated && isAuthRoute) {
      router.replace('/feed');
    }
  }, [isAuthenticated, isLoading, pathname, router]);

  // Block render until we know the auth state.
  // This prevents a flash of the login page for authenticated users.
  if (isLoading) {
    return <FullScreenLoader />;
  }

  return <>{children}</>;
}