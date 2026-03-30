// 📍 LOCATION: free-space/frontend/packages/api-client/src/instance.ts
//
// Core Axios instance with:
//  - JWT access token injection on every request
//  - Transparent token refresh on 401 (queues concurrent requests)
//  - Error normalisation → ApiException (mirrors backend BaseAPIException)
//  - Request ID header for backend structured logging correlation

import axios, { type AxiosInstance, type AxiosRequestConfig, type AxiosError } from 'axios';

import { ApiException, type ApiError } from '@qommunity/types';

// ─── Token store interface ─────────────────────────────────────────────────────
// Implemented differently per platform:
//   Web:    httpOnly cookie (handled by Next.js API route) + memory for access token
//   Mobile: expo-secure-store
// The api-client is token-store-agnostic — it calls these callbacks.
export interface TokenStore {
  getAccessToken: () => string | null;
  getRefreshToken: () => string | null;
  setTokens: (access: string, refresh: string) => void | Promise<void>;
  clearTokens: () => void | Promise<void>;
}

// ─── Global token store — set once at app init ────────────────────────────────
let _tokenStore: TokenStore | null = null;
let _onUnauthenticated: (() => void) | null = null;

export function configureApiClient(
  tokenStore: TokenStore,
  onUnauthenticated: () => void,
): void {
  _tokenStore = tokenStore;
  _onUnauthenticated = onUnauthenticated;
}

// ─── Axios instance ────────────────────────────────────────────────────────────
export const apiClient: AxiosInstance = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1',
  timeout: 15_000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
  withCredentials: true, // needed for httpOnly cookie refresh on web
});

// ─── Request interceptor — inject access token ────────────────────────────────
apiClient.interceptors.request.use(
  (config) => {
    const token = _tokenStore?.getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    // Correlate with backend RequestLoggingMiddleware
    config.headers['X-Request-ID'] = generateRequestId();
    return config;
  },
  (error: unknown) => Promise.reject(error),
);

// ─── Refresh queue — prevents multiple parallel refresh calls ─────────────────
let _isRefreshing = false;
let _refreshQueue: Array<{
  resolve: (token: string) => void;
  reject: (err: unknown) => void;
}> = [];

function processRefreshQueue(newToken: string | null, error: unknown = null): void {
  _refreshQueue.forEach(({ resolve, reject }) => {
    if (newToken) resolve(newToken);
    else reject(error);
  });
  _refreshQueue = [];
}

// ─── Response interceptor — handle 401, normalise errors ─────────────────────
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiError>) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

    // ── 401 Unauthorized: attempt token refresh ───────────────────────────────
    if (error.response?.status === 401 && !originalRequest._retry) {
      const refreshToken = _tokenStore?.getRefreshToken();

      if (!refreshToken) {
        _onUnauthenticated?.();
        return Promise.reject(normaliseError(error));
      }

      if (_isRefreshing) {
        // Queue this request until refresh completes
        return new Promise<string>((resolve, reject) => {
          _refreshQueue.push({ resolve, reject });
        })
          .then((newToken) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${newToken}`;
            }
            return apiClient(originalRequest);
          })
          .catch((err: unknown) => Promise.reject(err));
      }

      originalRequest._retry = true;
      _isRefreshing = true;

      try {
        const { data } = await axios.post<{ access: string }>(
          `${apiClient.defaults.baseURL}/users/auth/token/refresh/`,
          { refresh: refreshToken },
        );

        await _tokenStore?.setTokens(data.access, refreshToken);
        processRefreshQueue(data.access);

        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${data.access}`;
        }
        return apiClient(originalRequest);
      } catch (refreshError: unknown) {
        processRefreshQueue(null, refreshError);
        await _tokenStore?.clearTokens();
        _onUnauthenticated?.();
        return Promise.reject(normaliseError(error));
      } finally {
        _isRefreshing = false;
      }
    }

    return Promise.reject(normaliseError(error));
  },
);

// ─── Error normaliser — always throw ApiException ────────────────────────────
function normaliseError(error: AxiosError<ApiError>): ApiException {
  const status = error.response?.status ?? 0;
  const data = error.response?.data;

  // Backend returned a structured error
  if (data?.error_code) {
    return new ApiException(data, status);
  }

  // Network error or unexpected shape
  return new ApiException(
    {
      error_code: 'SERVER_ERROR',
      message: error.message || 'An unexpected error occurred.',
      details: {},
    },
    status,
  );
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
function generateRequestId(): string {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 9)}`;
}
