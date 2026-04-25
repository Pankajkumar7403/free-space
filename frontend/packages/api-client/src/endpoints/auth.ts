// 📍 LOCATION: free-space/frontend/packages/api-client/src/endpoints/auth.ts
//
// Auth API calls — map to backend apps/users/views.py auth endpoints
// Base URL: /api/v1/users/

import type {
    LoginPayload,
    LoginResponse,
    RegisterPayload,
    RegisterResponse,
    RefreshResponse,
    OAuthCallbackPayload,
    VerifyEmailPayload,
    ForgotPasswordPayload,
    ResetPasswordPayload,
  } from '@qommunity/types';
  
  import { apiClient } from '../instance';
  
  const BASE = '/users';
  
  export const authApi = {
    /**
     * POST /api/v1/users/login/
     * Returns user + JWT token pair.
     */
    login: async (payload: LoginPayload): Promise<LoginResponse> => {
      const { data } = await apiClient.post<LoginResponse>(`${BASE}/login/`, payload);
      return data;
    },
  
    /**
     * POST /api/v1/users/register/
     * Creates account and returns user + token pair.
     * Triggers email verification OTP via Celery.
     */
    register: async (payload: RegisterPayload): Promise<RegisterResponse> => {
      const { data } = await apiClient.post<RegisterResponse>(`${BASE}/register/`, payload);
      return data;
    },
  
    /**
     * POST /api/v1/users/logout/
     * Blacklists refresh token in Redis.
     */
    logout: async (refreshToken: string): Promise<void> => {
      await apiClient.post(`${BASE}/logout/`, { refresh: refreshToken });
    },
  
    /**
     * POST /api/v1/users/token/refresh/
     * Called transparently by the Axios interceptor — not typically called directly.
     */
    refreshToken: async (refreshToken: string): Promise<RefreshResponse> => {
      const { data } = await apiClient.post<RefreshResponse>(`${BASE}/token/refresh/`, {
        refresh: refreshToken,
      });
      return data;
    },
  
    /**
     * POST /api/v1/users/oauth/{provider}/
     * Handles Google and Apple OAuth2 callback.
     */
    oauthCallback: async (payload: OAuthCallbackPayload): Promise<LoginResponse> => {
      const { data } = await apiClient.post<LoginResponse>(
        `${BASE}/oauth/${payload.provider}/`,
        { code: payload.code, redirect_uri: payload.redirect_uri, state: payload.state },
      );
      return data;
    },
  
    /**
     * POST /api/v1/users/verify-email/
     * Verifies the OTP sent to the user's email.
     */
    verifyEmail: async (payload: VerifyEmailPayload): Promise<void> => {
      await apiClient.post(`${BASE}/verify-email/`, payload);
    },
  
    /**
     * POST /api/v1/users/verify-email/resend/
     * Re-sends the OTP. Rate-limited by backend.
     */
    resendVerificationEmail: async (): Promise<void> => {
      await apiClient.post(`${BASE}/verify-email/resend/`);
    },
  
    /**
     * POST /api/v1/users/forgot-password/
     * Sends OTP to email for password reset.
     */
    forgotPassword: async (payload: ForgotPasswordPayload): Promise<void> => {
      await apiClient.post(`${BASE}/forgot-password/`, payload);
    },
  
    /**
     * POST /api/v1/users/reset-password/
     */
    resetPassword: async (payload: ResetPasswordPayload): Promise<void> => {
      await apiClient.post(`${BASE}/reset-password/`, payload);
    },
  };
  