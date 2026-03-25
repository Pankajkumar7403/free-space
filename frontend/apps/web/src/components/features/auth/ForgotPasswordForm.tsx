// 📍 LOCATION: free-space/frontend/apps/web/src/components/features/auth/ForgotPasswordForm.tsx
//
// Two-step flow:
//  Step 1: Enter email → backend sends OTP
//  Step 2: Enter OTP + new password → reset complete

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Loader2, ArrowLeft, CheckCircle2 } from 'lucide-react';
import Link from 'next/link';

import {
  forgotPasswordSchema, type ForgotPasswordFormValues,
  resetPasswordSchema,  type ResetPasswordFormValues,
} from '@qommunity/validators';
import { authApi } from '@qommunity/api-client';
import { ApiException } from '@qommunity/types';

import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { FormError } from '@/components/ui/FormError';

type Step = 'email' | 'reset' | 'done';

export function ForgotPasswordForm() {
  const router        = useRouter();
  const [step, setStep]               = useState<Step>('email');
  const [submittedEmail, setEmail]    = useState('');
  const [serverError, setServerError] = useState<string | null>(null);

  // ── Step 1: Email form ──────────────────────────────────────────────────────
  const emailForm = useForm<ForgotPasswordFormValues>({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: { email: '' },
  });

  const onEmailSubmit = async ({ email }: ForgotPasswordFormValues) => {
    setServerError(null);
    try {
      await authApi.forgotPassword({ email });
      setEmail(email);
      setStep('reset');
    } catch (err) {
      // Don't reveal whether email exists — show generic message
      // (backend always returns 200 for security)
      setEmail(email);
      setStep('reset');
    }
  };

  // ── Step 2: OTP + new password form ────────────────────────────────────────
  const resetForm = useForm<ResetPasswordFormValues>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: { otp: '', new_password: '', confirm_password: '' },
  });

  const onResetSubmit = async (values: ResetPasswordFormValues) => {
    setServerError(null);
    try {
      await authApi.resetPassword({ otp: values.otp, new_password: values.new_password });
      setStep('done');
      setTimeout(() => router.push('/login'), 2000);
    } catch (err) {
      if (err instanceof ApiException) {
        if (err.isValidationError()) {
          const fieldErrors = err.getFieldErrors();
          Object.entries(fieldErrors).forEach(([field, message]) => {
            resetForm.setError(field as keyof ResetPasswordFormValues, { message });
          });
        } else {
          setServerError(err.message);
        }
      } else {
        setServerError('Something went wrong. Please try again.');
      }
    }
  };

  // ── Done ────────────────────────────────────────────────────────────────────
  if (step === 'done') {
    return (
      <div className="flex flex-col items-center gap-4 py-6 animate-in fade-in duration-300">
        <div className="rounded-full bg-green-100 dark:bg-green-900/30 p-4">
          <CheckCircle2 className="h-8 w-8 text-green-600 dark:text-green-400" aria-hidden="true" />
        </div>
        <h2 className="text-xl font-display font-semibold">Password reset!</h2>
        <p className="text-sm text-muted-foreground text-center">
          Redirecting you to sign in…
        </p>
      </div>
    );
  }

  // ── Step 2: Reset ───────────────────────────────────────────────────────────
  if (step === 'reset') {
    return (
      <div className="space-y-6 animate-in fade-in duration-300">
        <div className="space-y-1">
          <button
            onClick={() => setStep('email')}
            className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors mb-2"
            aria-label="Back to email step"
          >
            <ArrowLeft className="h-3.5 w-3.5" aria-hidden="true" /> Back
          </button>
          <h1 className="text-2xl font-display font-semibold tracking-tight">Set new password</h1>
          <p className="text-sm text-muted-foreground">
            Enter the code we sent to{' '}
            <span className="font-medium text-foreground">{submittedEmail}</span>
          </p>
        </div>

        {serverError && <FormError role="alert">{serverError}</FormError>}

        <form onSubmit={resetForm.handleSubmit(onResetSubmit)} noValidate className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="otp">Verification code</Label>
            <Input
              id="otp"
              inputMode="numeric"
              autoFocus
              placeholder="123456"
              maxLength={6}
              aria-invalid={!!resetForm.formState.errors.otp}
              {...resetForm.register('otp')}
            />
            {resetForm.formState.errors.otp && (
              <p className="text-xs text-destructive" role="alert">
                {resetForm.formState.errors.otp.message}
              </p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="new_password">New password</Label>
            <Input
              id="new_password"
              type="password"
              autoComplete="new-password"
              placeholder="Min. 8 characters"
              aria-invalid={!!resetForm.formState.errors.new_password}
              {...resetForm.register('new_password')}
            />
            {resetForm.formState.errors.new_password && (
              <p className="text-xs text-destructive" role="alert">
                {resetForm.formState.errors.new_password.message}
              </p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="confirm_password">Confirm new password</Label>
            <Input
              id="confirm_password"
              type="password"
              autoComplete="new-password"
              placeholder="Repeat password"
              aria-invalid={!!resetForm.formState.errors.confirm_password}
              {...resetForm.register('confirm_password')}
            />
            {resetForm.formState.errors.confirm_password && (
              <p className="text-xs text-destructive" role="alert">
                {resetForm.formState.errors.confirm_password.message}
              </p>
            )}
          </div>

          <Button
            type="submit"
            className="w-full"
            size="lg"
            disabled={resetForm.formState.isSubmitting}
          >
            {resetForm.formState.isSubmitting ? (
              <><Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />Resetting…</>
            ) : (
              'Reset password'
            )}
          </Button>
        </form>
      </div>
    );
  }

  // ── Step 1: Email ───────────────────────────────────────────────────────────
  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <div className="space-y-1">
        <h1 className="text-2xl font-display font-semibold tracking-tight">Forgot your password?</h1>
        <p className="text-sm text-muted-foreground">
          Enter your email and we&apos;ll send you a reset code.
        </p>
      </div>

      {serverError && <FormError role="alert">{serverError}</FormError>}

      <form onSubmit={emailForm.handleSubmit(onEmailSubmit)} noValidate className="space-y-4">
        <div className="space-y-1.5">
          <Label htmlFor="email">Email address</Label>
          <Input
            id="email"
            type="email"
            autoComplete="email"
            autoFocus
            placeholder="you@example.com"
            aria-invalid={!!emailForm.formState.errors.email}
            {...emailForm.register('email')}
          />
          {emailForm.formState.errors.email && (
            <p className="text-xs text-destructive" role="alert">
              {emailForm.formState.errors.email.message}
            </p>
          )}
        </div>

        <Button
          type="submit"
          className="w-full"
          size="lg"
          disabled={emailForm.formState.isSubmitting}
        >
          {emailForm.formState.isSubmitting ? (
            <><Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />Sending…</>
          ) : (
            'Send reset code'
          )}
        </Button>
      </form>

      <p className="text-center text-sm text-muted-foreground">
        Remembered it?{' '}
        <Link href="/login" className="font-medium text-primary hover:underline underline-offset-4">
          Sign in
        </Link>
      </p>
    </div>
  );
}
