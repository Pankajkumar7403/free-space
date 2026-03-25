// 📍 LOCATION: free-space/frontend/packages/types/src/auth.ts
//
// Auth types — mirror backend JWT + OAuth2 response shapes

import type { AuthenticatedUser } from './user';

// ─── JWT token pair — returned on login/register ──────────────────────────────
export interface TokenPair {
  access: string;    // short-lived (15 min)
  refresh: string;   // long-lived (30 days)
}

// ─── Login ────────────────────────────────────────────────────────────────────
export interface LoginPayload {
  email: string;
  password: string;
}

export interface LoginResponse {
  user: AuthenticatedUser;
  tokens: TokenPair;
}

// ─── Register ─────────────────────────────────────────────────────────────────
export interface RegisterPayload {
  username: string;
  email: string;
  password: string;
  display_name: string;
  // LGBTQ+ identity — all optional, private by default
  pronouns?: string;
  gender_identity?: string;
  sexual_orientation?: string;
}

export interface RegisterResponse {
  user: AuthenticatedUser;
  tokens: TokenPair;
  email_verification_sent: boolean;
}

// ─── Token refresh ────────────────────────────────────────────────────────────
export interface RefreshPayload {
  refresh: string;
}

export interface RefreshResponse {
  access: string;
}

// ─── OAuth2 social login ──────────────────────────────────────────────────────
export type OAuthProvider = 'google' | 'apple';

export interface OAuthCallbackPayload {
  provider: OAuthProvider;
  code: string;
  redirect_uri: string;
}

// ─── Email verification ───────────────────────────────────────────────────────
export interface VerifyEmailPayload {
  otp: string;
}

// ─── Password reset ───────────────────────────────────────────────────────────
export interface ForgotPasswordPayload {
  email: string;
}

export interface ResetPasswordPayload {
  otp: string;
  new_password: string;
}
