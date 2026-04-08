// 📍 LOCATION: free-space/frontend/apps/web/src/components/features/auth/OAuthButtons.tsx

'use client';

import { useState } from 'react';
import { Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/Button';

interface OAuthButtonsProps {
  callbackUrl: string;
}

export function OAuthButtons({ callbackUrl }: OAuthButtonsProps) {
  const [loading, setLoading] = useState<'google' | 'apple' | null>(null);

  const handleOAuth = async (provider: 'google' | 'apple') => {
    setLoading(provider);
    // Redirect to backend OAuth2 initiation endpoint
    // Backend: GET /api/v1/users/auth/oauth/{provider}/init/?redirect_uri=...
    const redirectUri = encodeURIComponent(
      `${window.location.origin}/api/users/oauth/callback?provider=${provider}&callbackUrl=${encodeURIComponent(callbackUrl)}`,
    );
    window.location.href = `/api/v1/users/auth/oauth/${provider}/init/?redirect_uri=${redirectUri}`;
  };

  return (
    <div className="grid grid-cols-2 gap-3">
      {/* Google */}
      <Button
        type="button"
        variant="outline"
        onClick={() => handleOAuth('google')}
        disabled={loading !== null}
        className="w-full"
        aria-label="Continue with Google"
      >
        {loading === 'google' ? (
          <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
        ) : (
          <>
            {/* Google G icon inline SVG */}
            <svg className="h-4 w-4 mr-2" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
            </svg>
            Google
          </>
        )}
      </Button>

      {/* Apple */}
      <Button
        type="button"
        variant="outline"
        onClick={() => handleOAuth('apple')}
        disabled={loading !== null}
        className="w-full"
        aria-label="Continue with Apple"
      >
        {loading === 'apple' ? (
          <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
        ) : (
          <>
            {/* Apple icon inline SVG */}
            <svg className="h-4 w-4 mr-2" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <path d="M16.52 0c.28 1.76-.51 3.5-1.49 4.74-.98 1.24-2.59 2.21-4.14 2.09-.31-1.64.55-3.35 1.49-4.52C13.37.99 15.05.1 16.52 0zm4.27 17.09c-.73 1.63-1.08 2.36-2.01 3.8-.93 1.44-2.27 3.25-3.91 3.26-1.46.02-1.84-.93-3.82-.92-1.98.01-2.4.95-3.87.94-1.65-.02-2.9-1.64-3.83-3.08C.83 17.27.17 12.2 2.3 9.27c1.47-2.07 3.79-3.28 5.98-3.28 1.57 0 2.96.95 3.97.95 1 0 2.55-1.16 4.3-.99.73.03 2.78.29 4.09 2.18-.11.07-2.44 1.4-2.41 4.18.04 3.31 2.93 4.41 3.06 4.78z"/>
            </svg>
            Apple
          </>
        )}
      </Button>
    </div>
  );
}
