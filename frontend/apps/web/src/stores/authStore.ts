//  LOCATION: free-space/frontend/apps/web/src/stores/authStore.ts
//
// Web Zustand auth store.
//
// Token strategy (web):
//   - Access token  -> memory only (this store). Lost on page refresh, immediately
//                     restored by AuthProvider calling /api/auth/session on mount.
//   - Refresh token -> httpOnly cookie set by /api/auth/set-cookie.
//                     The browser sends it automatically. JS cannot read it.
//                     This is XSS-safe: even if JS is compromised, it can't steal tokens.
//
// DO NOT import from '@/lib/session' in this file.
// DO NOT use localStorage or sessionStorage for tokens.

'use client';

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

import type { AuthenticatedUser } from '@qommunity/types';
import { configureApiClient } from '@qommunity/api-client';

// --- State shape --------------------------------------------------------------
interface AuthState {
  user: AuthenticatedUser | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  setAuth: (user: AuthenticatedUser, accessToken: string) => void;
  updateUser: (updates: Partial<AuthenticatedUser>) => void;
  clearAuth: () => void;
  setLoading: (loading: boolean) => void;
}

// --- Store --------------------------------------------------------------------
export const useAuthStore = create<AuthState>()(
  devtools(
    (set, get) => ({
      user:            null,
      accessToken:     null,
      isAuthenticated: false,
      isLoading:       true,   // true until AuthProvider restores session on mount

      // Called after: login, register, session restore
      setAuth: (user, accessToken) => {
        set(
          { user, accessToken, isAuthenticated: true, isLoading: false },
          false,
          'auth/setAuth',
        );

        // Wire the api-client Axios interceptor to read tokens from this store.
        // Web: refresh token is in httpOnly cookie, the /api/auth/session route
        // handles refreshing it - so getRefreshToken returns null here.
        configureApiClient(
          {
            getAccessToken:  () => get().accessToken,
            getRefreshToken: () => null,
            setTokens: (newAccess) => {
              set({ accessToken: newAccess }, false, 'auth/tokenRefreshed');
            },
            clearTokens: () => {
              get().clearAuth();
            },
          },
          // onUnauthenticated - called when refresh fails
          () => get().clearAuth(),
        );
      },

      // Called after profile edits
      updateUser: (updates) =>
        set(
          (state) => ({
            user: state.user ? { ...state.user, ...updates } : null,
          }),
          false,
          'auth/updateUser',
        ),

      // Called on logout or session expiry
      clearAuth: () =>
        set(
          { user: null, accessToken: null, isAuthenticated: false, isLoading: false },
          false,
          'auth/clearAuth',
        ),

      setLoading: (loading) =>
        set({ isLoading: loading }, false, 'auth/setLoading'),
    }),
    {
      name: 'AuthStore',
      enabled: process.env.NODE_ENV === 'development',
    },
  ),
);

// --- Selectors - always use these in components, never select the whole store -
export const selectUser            = (s: AuthState) => s.user;
export const selectIsAuthenticated = (s: AuthState) => s.isAuthenticated;
export const selectIsLoading       = (s: AuthState) => s.isLoading;
export const selectAccessToken     = (s: AuthState) => s.accessToken;