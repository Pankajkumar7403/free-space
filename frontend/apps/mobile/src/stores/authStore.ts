// 📍 LOCATION: free-space/frontend/apps/mobile/src/stores/authStore.ts
//
// Zustand auth store for React Native.
// Mirrors the web authStore but uses SecureStore for token persistence.

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

import type { AuthenticatedUser } from '@qommunity/types';
import { configureApiClient } from '@qommunity/api-client';
import {
  saveTokens,
  clearStoredTokens,
  setCachedTokens,
  clearCachedTokens,
  getCachedAccessToken,
  getCachedRefreshToken,
} from '@/lib/session';

interface AuthState {
  // State
  user: AuthenticatedUser | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  // Actions
  setAuth: (user: AuthenticatedUser, accessToken: string, refreshToken?: string) => void;
  updateUser: (updates: Partial<AuthenticatedUser>) => void;
  clearAuth: () => void;
  setLoading: (loading: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
  devtools(
    (set, get) => ({
      user:            null,
      accessToken:     null,
      isAuthenticated: false,
      isLoading:       true,

      setAuth: (user, accessToken, refreshToken) => {
        set(
          { user, accessToken, isAuthenticated: true, isLoading: false },
          false,
          'auth/setAuth',
        );

        setCachedTokens(accessToken, refreshToken ?? getCachedRefreshToken());

        if (refreshToken) {
          void saveTokens(accessToken, refreshToken);
        }

        configureApiClient(
          {
            getAccessToken:  getCachedAccessToken,
            getRefreshToken: getCachedRefreshToken,
            setTokens: (access, refresh) => {
              setCachedTokens(access, refresh);
              void saveTokens(access, refresh);
              set({ accessToken: access }, false, 'auth/tokenRefreshed');
            },
            clearTokens: () => {
              clearCachedTokens();
              void clearStoredTokens();
              get().clearAuth();
            },
          },
          () => get().clearAuth(),
        );
      },

      updateUser: (updates) =>
        set(
          (state) => ({
            user: state.user ? { ...state.user, ...updates } : null,
          }),
          false,
          'auth/updateUser',
        ),

      clearAuth: () => {
        clearCachedTokens();
        set(
          { user: null, accessToken: null, isAuthenticated: false, isLoading: false },
          false,
          'auth/clearAuth',
        );
      },

      setLoading: (loading) => set({ isLoading: loading }, false, 'auth/setLoading'),
    }),
    { name: 'MobileAuthStore', enabled: __DEV__ },
  ),
);

// Selectors — stable references, prevent unnecessary re-renders
export const selectUser            = (s: AuthState) => s.user;
export const selectIsAuthenticated = (s: AuthState) => s.isAuthenticated;
export const selectIsLoading       = (s: AuthState) => s.isLoading;