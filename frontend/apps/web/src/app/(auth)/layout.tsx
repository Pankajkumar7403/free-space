// 📍 LOCATION: free-space/frontend/apps/web/src/app/(auth)/layout.tsx
//
// Unauthenticated layout — centred card with pride gradient background.
// Wraps: /login, /register, /forgot-password, /reset-password, /verify-email

import type { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  robots: { index: false }, // Don't index auth pages
};

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Pride gradient strip at top */}
      <div className="h-1 pride-gradient w-full flex-shrink-0" aria-hidden="true" />

      <div className="flex flex-1 items-center justify-center px-4 py-12">
        <div className="w-full max-w-[400px] space-y-8">
          {/* Logo */}
          <div className="text-center space-y-2">
            <Link href="/" className="inline-block group" aria-label="Qommunity home">
              <span className="text-4xl font-display font-bold tracking-tight text-foreground group-hover:text-primary transition-colors">
                Q
                <span className="text-primary">ommunity</span>
              </span>
            </Link>
            <p className="text-sm text-muted-foreground font-sans">
              Your space. Your pride.{' '}
              <span aria-hidden="true">🏳️‍🌈</span>
            </p>
          </div>

          {/* Auth form card */}
          <div className="glass-card rounded-2xl p-8 shadow-lg">
            {children}
          </div>

          {/* Footer */}
          <p className="text-center text-xs text-muted-foreground">
            By continuing, you agree to our{' '}
            <Link href="/terms" className="underline underline-offset-4 hover:text-foreground transition-colors">
              Terms
            </Link>{' '}
            and{' '}
            <Link href="/privacy" className="underline underline-offset-4 hover:text-foreground transition-colors">
              Privacy Policy
            </Link>
            .
          </p>
        </div>
      </div>
    </div>
  );
}
