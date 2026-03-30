// 📍 LOCATION: free-space/frontend/apps/web/src/components/features/auth/VerifyEmailForm.tsx
//
// 6-digit OTP input for email verification.
// Each digit is a separate input for native UX feel — auto-advances on input.

'use client';

import { useRef, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Loader2, MailCheck } from 'lucide-react';

import { authApi } from '@qommunity/api-client';
import { ApiException } from '@qommunity/types';

import { useAuthStore } from '@/stores/authStore';
import { Button } from '@/components/ui/Button';
import { FormError } from '@/components/ui/FormError';

const OTP_LENGTH = 6;

export function VerifyEmailForm() {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);

  const [digits, setDigits]         = useState<string[]>(Array(OTP_LENGTH).fill(''));
  const [isSubmitting, setSubmitting] = useState(false);
  const [isResending, setResending]  = useState(false);
  const [resendCooldown, setCooldown] = useState(0);
  const [error, setError]            = useState<string | null>(null);
  const [success, setSuccess]        = useState(false);

  const inputRefs = useRef<Array<HTMLInputElement | null>>(Array(OTP_LENGTH).fill(null));
  const cooldownRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // ── Digit input handler ─────────────────────────────────────────────────────
  const handleDigitChange = useCallback(
    (index: number, value: string) => {
      const cleaned = value.replace(/\D/g, '').slice(-1); // digits only, last char
      const next = [...digits];
      next[index] = cleaned;
      setDigits(next);
      setError(null);

      // Auto-advance
      if (cleaned && index < OTP_LENGTH - 1) {
        inputRefs.current[index + 1]?.focus();
      }

      // Auto-submit when all filled
      if (cleaned && next.every(Boolean)) {
        void submitOtp(next.join(''));
      }
    },
    [digits], // eslint-disable-line react-hooks/exhaustive-deps
  );

  const handleKeyDown = useCallback(
    (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Backspace' && !digits[index] && index > 0) {
        inputRefs.current[index - 1]?.focus();
      }
    },
    [digits],
  );

  const handlePaste = useCallback(
    (e: React.ClipboardEvent) => {
      e.preventDefault();
      const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, OTP_LENGTH);
      if (!pasted) return;
      const next = [...Array(OTP_LENGTH).fill('')];
      pasted.split('').forEach((ch, i) => { next[i] = ch; });
      setDigits(next);
      inputRefs.current[Math.min(pasted.length, OTP_LENGTH - 1)]?.focus();
      if (pasted.length === OTP_LENGTH) void submitOtp(pasted);
    },
    [], // eslint-disable-line react-hooks/exhaustive-deps
  );

  // ── Submit ──────────────────────────────────────────────────────────────────
  const submitOtp = async (otp: string) => {
    setSubmitting(true);
    setError(null);
    try {
      await authApi.verifyEmail({ otp });
      setSuccess(true);
      setTimeout(() => router.push('/feed'), 1500);
    } catch (err) {
      const message = err instanceof ApiException ? err.message : 'Invalid code. Please try again.';
      setError(message);
      setDigits(Array(OTP_LENGTH).fill(''));
      inputRefs.current[0]?.focus();
    } finally {
      setSubmitting(false);
    }
  };

  // ── Resend ──────────────────────────────────────────────────────────────────
  const handleResend = async () => {
    setResending(true);
    setError(null);
    try {
      await authApi.resendVerificationEmail();
      // Start 60s cooldown
      setCooldown(60);
      cooldownRef.current = setInterval(() => {
        setCooldown((c) => {
          if (c <= 1) {
            clearInterval(cooldownRef.current!);
            return 0;
          }
          return c - 1;
        });
      }, 1000);
    } catch (err) {
      setError(err instanceof ApiException ? err.message : 'Failed to resend. Try again shortly.');
    } finally {
      setResending(false);
    }
  };

  // ── Success state ───────────────────────────────────────────────────────────
  if (success) {
    return (
      <div className="flex flex-col items-center gap-4 py-4 animate-in fade-in duration-300">
        <div className="rounded-full bg-green-100 dark:bg-green-900/30 p-4">
          <MailCheck className="h-8 w-8 text-green-600 dark:text-green-400" aria-hidden="true" />
        </div>
        <p className="text-center font-medium">Email verified! Redirecting…</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <div className="space-y-2 text-center">
        <h1 className="text-2xl font-display font-semibold tracking-tight">Check your email</h1>
        <p className="text-sm text-muted-foreground">
          We sent a 6-digit code to{' '}
          <span className="font-medium text-foreground">{user?.email ?? 'your email'}</span>
        </p>
      </div>

      {error && <FormError role="alert" aria-live="assertive">{error}</FormError>}

      {/* OTP digit inputs */}
      <div
        className="flex justify-center gap-2"
        role="group"
        aria-label="One-time password input"
        onPaste={handlePaste}
      >
        {digits.map((digit, i) => (
          <input
            key={i}
            ref={(el) => { inputRefs.current[i] = el; }}
            type="text"
            inputMode="numeric"
            maxLength={1}
            value={digit}
            onChange={(e) => handleDigitChange(i, e.target.value)}
            onKeyDown={(e) => handleKeyDown(i, e)}
            disabled={isSubmitting}
            aria-label={`Digit ${i + 1} of ${OTP_LENGTH}`}
            className="
              h-14 w-12 rounded-xl border-2 border-input bg-background
              text-center text-2xl font-bold font-mono
              transition-all duration-150
              focus:border-primary focus:ring-2 focus:ring-ring focus:ring-offset-2 focus:outline-none
              disabled:opacity-50
              aria-[invalid=true]:border-destructive
            "
            aria-invalid={!!error}
          />
        ))}
      </div>

      <Button
        type="button"
        className="w-full"
        size="lg"
        disabled={isSubmitting || digits.filter(Boolean).length < OTP_LENGTH}
        onClick={() => void submitOtp(digits.join(''))}
      >
        {isSubmitting ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />
            Verifying…
          </>
        ) : (
          'Verify email'
        )}
      </Button>

      <div className="text-center">
        <p className="text-sm text-muted-foreground mb-2">Didn&apos;t receive the code?</p>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          disabled={isResending || resendCooldown > 0}
          onClick={handleResend}
        >
          {isResending ? (
            <><Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" aria-hidden="true" />Sending…</>
          ) : resendCooldown > 0 ? (
            `Resend in ${resendCooldown}s`
          ) : (
            'Resend code'
          )}
        </Button>
      </div>
    </div>
  );
}
