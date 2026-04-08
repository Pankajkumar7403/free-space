//  LOCATION: free-space/frontend/apps/web/src/components/features/auth/RegisterForm.tsx
//
// Registration form with LGBTQ+ identity fields.
// Identity fields are optional and private by default - clearly communicated to user.

'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Eye, EyeOff, Loader2, ChevronDown, Info } from 'lucide-react';

import { registerSchema, type RegisterFormValues } from '@qommunity/validators';
import { PRONOUNS, GENDER_IDENTITY, SEXUAL_ORIENTATION, ApiException } from '@qommunity/types';
import { authApi } from '@qommunity/api-client';

import { useAuthStore } from '@/stores/authStore';
import { persistRefreshToken } from '@/lib/session';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Select } from '@/components/ui/Select';
import { FormError } from '@/components/ui/FormError';
import { OAuthButtons } from '@/components/features/auth/OAuthButtons';
import { Separator } from '@/components/ui/Separator';
import { Tooltip } from '@/components/ui/Tooltip';
import { cn } from '@/lib/utils';

export function RegisterForm() {
  const router  = useRouter();
  const setAuth = useAuthStore((s) => s.setAuth);

  const [showPassword, setShowPassword]         = useState(false);
  const [showIdentity, setShowIdentity]         = useState(false);
  const [serverError, setServerError]           = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      username: '',
      email: '',
      display_name: '',
      password: '',
      confirm_password: '',
    },
  });

  const onSubmit = async (values: RegisterFormValues) => {
    setServerError(null);
    try {
      const { user, tokens } = await authApi.register({
        username:           values.username,
        email:              values.email,
        display_name:       values.display_name,
        password:           values.password,
        pronouns:           values.pronouns,
        gender_identity:    values.gender_identity,
        sexual_orientation: values.sexual_orientation,
      });

      setAuth(user, tokens.access);

      await persistRefreshToken(tokens.refresh);

      // Redirect to email verification
      router.push('/verify-email');
    } catch (error) {
      if (error instanceof ApiException) {
        if (error.isValidationError()) {
          const fieldErrors = error.getFieldErrors();
          Object.entries(fieldErrors).forEach(([field, message]) => {
            setError(field as keyof RegisterFormValues, { message });
          });
        } else {
          setServerError(error.message);
        }
      } else {
        setServerError('Something went wrong. Please try again.');
      }
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <div className="space-y-1">
        <h1 className="text-2xl font-display font-semibold tracking-tight">Join Qommunity</h1>
        <p className="text-sm text-muted-foreground">Your safe space starts here </p>
      </div>

      <OAuthButtons callbackUrl="/feed" />
      <Separator label="or register with email" />

      <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
        {serverError && (
          <FormError role="alert" aria-live="polite">{serverError}</FormError>
        )}

        {/* Display name */}
        <div className="space-y-1.5">
          <Label htmlFor="display_name">Display name</Label>
          <Input
            id="display_name"
            autoFocus
            placeholder="Your name"
            aria-invalid={!!errors.display_name}
            {...register('display_name')}
          />
          {errors.display_name && (
            <p className="text-xs text-destructive" role="alert">{errors.display_name.message}</p>
          )}
        </div>

        {/* Username */}
        <div className="space-y-1.5">
          <Label htmlFor="username">Username</Label>
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground text-sm select-none">@</span>
            <Input
              id="username"
              className="pl-7"
              autoComplete="username"
              placeholder="yourhandle"
              aria-invalid={!!errors.username}
              {...register('username')}
            />
          </div>
          {errors.username && (
            <p className="text-xs text-destructive" role="alert">{errors.username.message}</p>
          )}
        </div>

        {/* Email */}
        <div className="space-y-1.5">
          <Label htmlFor="email">Email address</Label>
          <Input
            id="email"
            type="email"
            autoComplete="email"
            placeholder="you@example.com"
            aria-invalid={!!errors.email}
            {...register('email')}
          />
          {errors.email && (
            <p className="text-xs text-destructive" role="alert">{errors.email.message}</p>
          )}
        </div>

        {/* Password */}
        <div className="space-y-1.5">
          <Label htmlFor="password">Password</Label>
          <div className="relative">
            <Input
              id="password"
              type={showPassword ? 'text' : 'password'}
              autoComplete="new-password"
              placeholder="Min. 8 characters"
              className="pr-10"
              aria-invalid={!!errors.password}
              {...register('password')}
            />
            <button
              type="button"
              onClick={() => setShowPassword((v) => !v)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
              aria-label={showPassword ? 'Hide password' : 'Show password'}
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          {errors.password && (
            <p className="text-xs text-destructive" role="alert">{errors.password.message}</p>
          )}
        </div>

        {/* Confirm password */}
        <div className="space-y-1.5">
          <Label htmlFor="confirm_password">Confirm password</Label>
          <Input
            id="confirm_password"
            type={showPassword ? 'text' : 'password'}
            autoComplete="new-password"
            placeholder="Repeat password"
            aria-invalid={!!errors.confirm_password}
            {...register('confirm_password')}
          />
          {errors.confirm_password && (
            <p className="text-xs text-destructive" role="alert">{errors.confirm_password.message}</p>
          )}
        </div>

        {/* -- LGBTQ+ Identity section (optional, collapsible) --------------- */}
        <div className="rounded-xl border border-border bg-muted/30 overflow-hidden">
          <button
            type="button"
            onClick={() => setShowIdentity((v) => !v)}
            className="w-full flex items-center justify-between px-4 py-3 text-sm font-medium hover:bg-muted/50 transition-colors"
            aria-expanded={showIdentity}
            aria-controls="identity-fields"
          >
            <span className="flex items-center gap-2">
              <span aria-hidden="true"></span>
              Identity & pronouns
              <span className="text-xs font-normal text-muted-foreground">(optional)</span>
            </span>
            <ChevronDown
              className={cn('h-4 w-4 text-muted-foreground transition-transform', showIdentity && 'rotate-180')}
              aria-hidden="true"
            />
          </button>

          {showIdentity && (
            <div id="identity-fields" className="px-4 pb-4 space-y-4 border-t border-border pt-4">
              {/* Privacy note */}
              <div className="flex gap-2 text-xs text-muted-foreground bg-primary/5 rounded-lg p-3">
                <Info className="h-3.5 w-3.5 flex-shrink-0 mt-0.5 text-primary" aria-hidden="true" />
                <span>
                  These fields are <strong>private by default</strong> - only followers you approve
                  can see them. You can change visibility per-field anytime in settings.
                </span>
              </div>

              {/* Pronouns */}
              <div className="space-y-1.5">
                <Label htmlFor="pronouns">Pronouns</Label>
                <Select id="pronouns" {...register('pronouns')}>
                  <option value="">Select pronouns</option>
                  {PRONOUNS.map((p) => (
                    <option key={p} value={p}>{p}</option>
                  ))}
                </Select>
              </div>

              {/* Gender identity */}
              <div className="space-y-1.5">
                <Label htmlFor="gender_identity">Gender identity</Label>
                <Select id="gender_identity" {...register('gender_identity')}>
                  <option value="">Select gender identity</option>
                  {GENDER_IDENTITY.map((g) => (
                    <option key={g} value={g}>{g.replace(/_/g, ' ')}</option>
                  ))}
                </Select>
              </div>

              {/* Sexual orientation */}
              <div className="space-y-1.5">
                <Label htmlFor="sexual_orientation">Sexual orientation</Label>
                <Select id="sexual_orientation" {...register('sexual_orientation')}>
                  <option value="">Select orientation</option>
                  {SEXUAL_ORIENTATION.map((o) => (
                    <option key={o} value={o}>{o.replace(/_/g, ' ')}</option>
                  ))}
                </Select>
              </div>
            </div>
          )}
        </div>

        <Button type="submit" className="w-full" disabled={isSubmitting} size="lg">
          {isSubmitting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />
              Creating account
            </>
          ) : (
            'Create account'
          )}
        </Button>
      </form>

      <p className="text-center text-sm text-muted-foreground">
        Already have an account?{' '}
        <Link href="/login" className="font-medium text-primary hover:underline underline-offset-4">
          Sign in
        </Link>
      </p>
    </div>
  );
}