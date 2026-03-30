// 📍 LOCATION: free-space/frontend/apps/web/src/app/error.tsx
//
// Next.js error boundary — catches unhandled errors in the app shell.
// Sentry will capture these in production.

'use client';

import { useEffect } from 'react';
import { Button } from '@/components/ui/Button';

interface ErrorPageProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function GlobalError({ error, reset }: ErrorPageProps) {
  useEffect(() => {
    // TODO Sprint 8: Sentry.captureException(error)
    console.error('Unhandled error:', error);
  }, [error]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center gap-6 px-4">
      <div className="text-center space-y-3 max-w-md">
        <p className="text-5xl" aria-hidden="true">😕</p>
        <h1 className="text-2xl font-display font-semibold">Something went wrong</h1>
        <p className="text-sm text-muted-foreground">
          An unexpected error occurred. Our team has been notified.
        </p>
        {process.env.NODE_ENV === 'development' && (
          <pre className="mt-4 text-left text-xs bg-muted rounded-lg p-4 overflow-auto max-h-48 text-destructive">
            {error.message}
          </pre>
        )}
      </div>
      <div className="flex gap-3">
        <Button onClick={reset} variant="default">Try again</Button>
        <Button onClick={() => (window.location.href = '/')} variant="outline">Go home</Button>
      </div>
    </div>
  );
}
