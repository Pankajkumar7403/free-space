// 📍 LOCATION: free-space/frontend/apps/mobile/src/lib/session.ts
//
// Mobile session management using expo-secure-store.
// Tokens are encrypted by the OS keychain (iOS) / Android Keystore.
// Never use AsyncStorage for tokens — it is NOT encrypted.

import * as SecureStore from 'expo-secure-store';
import type { AuthenticatedUser } from '@qommunity/types';

// ─── Storage keys ─────────────────────────────────────────────────────────────
const KEYS = {
  ACCESS_TOKEN:  'qommunity_access',
  REFRESH_TOKEN: 'qommunity_refresh',
} as const;

// ─── SecureStore helpers ──────────────────────────────────────────────────────
export async function saveTokens(access: string, refresh: string): Promise<void> {
  await Promise.all([
    SecureStore.setItemAsync(KEYS.ACCESS_TOKEN,  access),
    SecureStore.setItemAsync(KEYS.REFRESH_TOKEN, refresh),
  ]);
}

export async function getStoredTokens(): Promise<{ access: string | null; refresh: string | null }> {
  const [access, refresh] = await Promise.all([
    SecureStore.getItemAsync(KEYS.ACCESS_TOKEN),
    SecureStore.getItemAsync(KEYS.REFRESH_TOKEN),
  ]);
  return { access, refresh };
}

export async function clearStoredTokens(): Promise<void> {
  await Promise.all([
    SecureStore.deleteItemAsync(KEYS.ACCESS_TOKEN),
    SecureStore.deleteItemAsync(KEYS.REFRESH_TOKEN),
  ]);
}

// ─── Session restore deps — defined inline to break circular import ───────────
interface RestoreSessionDeps {
  setAuth: (user: AuthenticatedUser, accessToken: string, refreshToken?: string) => void;
  clearAuth: () => void;
  setLoading: (loading: boolean) => void;
}

const API_BASE = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';

export async function restoreSession({
  setAuth,
  clearAuth,
  setLoading,
}: RestoreSessionDeps): Promise<void> {
  setLoading(true);

  try {
    const { refresh } = await getStoredTokens();

    if (!refresh) {
      clearAuth();
      return;
    }

    const refreshRes = await fetch(`${API_BASE}/users/auth/token/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh }),
    });

    if (!refreshRes.ok) {
      await clearStoredTokens();
      clearAuth();
      return;
    }

    const { access } = (await refreshRes.json()) as { access: string };

    const meRes = await fetch(`${API_BASE}/users/me/`, {
      headers: { Authorization: `Bearer ${access}` },
    });

    if (!meRes.ok) {
      await clearStoredTokens();
      clearAuth();
      return;
    }

    const user = (await meRes.json()) as AuthenticatedUser;
    await SecureStore.setItemAsync(KEYS.ACCESS_TOKEN, access);
    setAuth(user, access, refresh);
  } catch {
    await clearStoredTokens();
    clearAuth();
  }
}

// ─── In-memory token cache — synchronous access for api-client interceptor ────
let _cachedAccessToken:  string | null = null;
let _cachedRefreshToken: string | null = null;

export function getCachedAccessToken():  string | null { return _cachedAccessToken;  }
export function getCachedRefreshToken(): string | null { return _cachedRefreshToken; }

export function setCachedTokens(access: string, refresh: string | null): void {
  _cachedAccessToken  = access;
  _cachedRefreshToken = refresh;
}

export function clearCachedTokens(): void {
  _cachedAccessToken  = null;
  _cachedRefreshToken = null;
}