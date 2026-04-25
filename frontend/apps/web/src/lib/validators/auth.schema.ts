// 📍 LOCATION: free-space/frontend/packages/validators/src/auth.schema.ts
//
// Auth Zod schemas — rules must stay in sync with backend validators.py
// If backend changes a rule (e.g. min password length), update here too.

import { z } from 'zod';

import { PRONOUNS, GENDER_IDENTITY, SEXUAL_ORIENTATION } from '@qommunity/types';

// ─── Reusable primitives ──────────────────────────────────────────────────────

/** Password rules: min 8 chars, 1 uppercase, 1 lowercase, 1 digit — mirrors backend */
const passwordSchema = z
  .string()
  .min(8, 'Password must be at least 8 characters')
  .max(128, 'Password is too long')
  .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
  .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
  .regex(/[0-9]/, 'Password must contain at least one number');

/** Username: 3–30 chars, alphanumeric + underscore, no leading/trailing underscore */
const usernameSchema = z
  .string()
  .min(3, 'Username must be at least 3 characters')
  .max(30, 'Username must be 30 characters or fewer')
  .regex(
    /^[a-zA-Z0-9]([a-zA-Z0-9_]*[a-zA-Z0-9])?$/,
    'Username can only contain letters, numbers, and underscores',
  );

// ─── Login ────────────────────────────────────────────────────────────────────
export const loginSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  password: z.string().min(1, 'Password is required'),
});

export type LoginFormValues = z.infer<typeof loginSchema>;

// ─── Register ─────────────────────────────────────────────────────────────────
export const registerSchema = z
  .object({
    username: usernameSchema,
    email: z.string().email('Please enter a valid email address'),
    display_name: z
      .string()
      .min(1, 'Display name is required')
      .max(60, 'Display name must be 60 characters or fewer'),
    password: passwordSchema,
    confirm_password: z.string(),

    // LGBTQ+ identity — all optional, private by default
    pronouns: z.enum(PRONOUNS).optional(),
    gender_identity: z.enum(GENDER_IDENTITY).optional(),
    sexual_orientation: z.enum(SEXUAL_ORIENTATION).optional(),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: 'Passwords do not match',
    path: ['confirm_password'],
  });

export type RegisterFormValues = z.infer<typeof registerSchema>;

// ─── Email OTP verify ────────────────────────────────────────────────────────
export const verifyEmailSchema = z.object({
  otp: z
    .string()
    .length(6, 'Verification code must be 6 digits')
    .regex(/^\d+$/, 'Verification code must be digits only'),
});

export type VerifyEmailFormValues = z.infer<typeof verifyEmailSchema>;

// ─── Forgot password ──────────────────────────────────────────────────────────
export const forgotPasswordSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
});

export type ForgotPasswordFormValues = z.infer<typeof forgotPasswordSchema>;

// ─── Reset password ───────────────────────────────────────────────────────────
export const resetPasswordSchema = z
  .object({
    otp: z
      .string()
      .length(6, 'Verification code must be 6 digits')
      .regex(/^\d+$/, 'Verification code must be digits only'),
    new_password: passwordSchema,
    confirm_password: z.string(),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: 'Passwords do not match',
    path: ['confirm_password'],
  });

export type ResetPasswordFormValues = z.infer<typeof resetPasswordSchema>;
