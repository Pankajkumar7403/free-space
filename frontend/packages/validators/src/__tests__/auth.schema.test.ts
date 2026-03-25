// 📍 LOCATION: free-space/frontend/packages/validators/src/__tests__/auth.schema.test.ts
//
// Tests for auth Zod schemas.
// Naming convention: test_{what}_{condition}
// Pattern: Arrange → Act → Assert (no describe nesting beyond 2 levels)

import { describe, it, expect } from 'vitest';
import { loginSchema, registerSchema, verifyEmailSchema, resetPasswordSchema } from '../auth.schema';

// ─── loginSchema ──────────────────────────────────────────────────────────────
describe('loginSchema', () => {
  it('accepts valid email and password', () => {
    const result = loginSchema.safeParse({
      email:    'user@example.com',
      password: 'anypassword',
    });
    expect(result.success).toBe(true);
  });

  it('rejects invalid email format', () => {
    const result = loginSchema.safeParse({ email: 'not-an-email', password: 'pass' });
    expect(result.success).toBe(false);
    expect(result.error?.flatten().fieldErrors.email).toBeDefined();
  });

  it('rejects empty email', () => {
    const result = loginSchema.safeParse({ email: '', password: 'pass' });
    expect(result.success).toBe(false);
  });

  it('rejects empty password', () => {
    const result = loginSchema.safeParse({ email: 'user@example.com', password: '' });
    expect(result.success).toBe(false);
    expect(result.error?.flatten().fieldErrors.password).toBeDefined();
  });
});

// ─── registerSchema ───────────────────────────────────────────────────────────
describe('registerSchema', () => {
  const validPayload = {
    username:         'validuser',
    email:            'valid@example.com',
    display_name:     'Valid User',
    password:         'SecurePass1',
    confirm_password: 'SecurePass1',
  };

  it('accepts valid registration payload', () => {
    const result = registerSchema.safeParse(validPayload);
    expect(result.success).toBe(true);
  });

  it('accepts payload with optional LGBTQ+ identity fields', () => {
    const result = registerSchema.safeParse({
      ...validPayload,
      pronouns:           'they/them',
      gender_identity:    'non_binary',
      sexual_orientation: 'queer',
    });
    expect(result.success).toBe(true);
  });

  it('rejects username shorter than 3 characters', () => {
    const result = registerSchema.safeParse({ ...validPayload, username: 'ab' });
    expect(result.success).toBe(false);
    expect(result.error?.flatten().fieldErrors.username).toBeDefined();
  });

  it('rejects username longer than 30 characters', () => {
    const result = registerSchema.safeParse({
      ...validPayload,
      username: 'a'.repeat(31),
    });
    expect(result.success).toBe(false);
  });

  it('rejects username with special characters', () => {
    const result = registerSchema.safeParse({ ...validPayload, username: 'user@name' });
    expect(result.success).toBe(false);
  });

  it('rejects password without uppercase letter', () => {
    const result = registerSchema.safeParse({ ...validPayload, password: 'nouppercase1', confirm_password: 'nouppercase1' });
    expect(result.success).toBe(false);
    expect(result.error?.flatten().fieldErrors.password).toBeDefined();
  });

  it('rejects password without digit', () => {
    const result = registerSchema.safeParse({ ...validPayload, password: 'NoDigitHere', confirm_password: 'NoDigitHere' });
    expect(result.success).toBe(false);
  });

  it('rejects password shorter than 8 characters', () => {
    const result = registerSchema.safeParse({ ...validPayload, password: 'Short1', confirm_password: 'Short1' });
    expect(result.success).toBe(false);
  });

  it('rejects when passwords do not match', () => {
    const result = registerSchema.safeParse({
      ...validPayload,
      password:         'SecurePass1',
      confirm_password: 'DifferentPass1',
    });
    expect(result.success).toBe(false);
    expect(result.error?.flatten().fieldErrors.confirm_password).toBeDefined();
  });

  it('rejects display_name longer than 60 characters', () => {
    const result = registerSchema.safeParse({ ...validPayload, display_name: 'A'.repeat(61) });
    expect(result.success).toBe(false);
  });
});

// ─── verifyEmailSchema ────────────────────────────────────────────────────────
describe('verifyEmailSchema', () => {
  it('accepts 6-digit OTP', () => {
    expect(verifyEmailSchema.safeParse({ otp: '123456' }).success).toBe(true);
  });

  it('rejects OTP shorter than 6 digits', () => {
    expect(verifyEmailSchema.safeParse({ otp: '12345' }).success).toBe(false);
  });

  it('rejects OTP longer than 6 digits', () => {
    expect(verifyEmailSchema.safeParse({ otp: '1234567' }).success).toBe(false);
  });

  it('rejects non-digit OTP', () => {
    expect(verifyEmailSchema.safeParse({ otp: '12345a' }).success).toBe(false);
  });
});
