//  LOCATION: free-space/frontend/apps/web/src/components/providers/AuthProvider.tsx
//
// Restores auth session on every page load from the httpOnly refresh cookie.
// Shows FullScreenLoader while loading to prevent a flash of the login page
// for users who are already authenticated.

'use client';

import { useEffect } from 'react';
import { useAuthStore } from '@/stores/authStore';
import { fetchSession } from '@/lib/session';
import { FullScreenLoader } from '@/components/ui/FullScreenLoader';

interface AuthProviderProps {
  children: React.ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const setAuth    = useAuthStore((s) => s.setAuth);
  const clearAuth  = useAuthStore((s) => s.clearAuth);
  const isLoading  = useAuthStore((s) => s.isLoading);

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

  // Block render until we know the auth state.
  // This prevents a flash of the login page for authenticated users.
  if (isLoading) {
    return <FullScreenLoader />;
  }

  return <>{children}</>;
}