// 📍 LOCATION: free-space/frontend/apps/web/src/components/providers/AppProviders.tsx
//
// Client boundary for all context providers.
// Kept separate from layout.tsx so the root layout stays a Server Component.

'use client';

import { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

import { ToastProvider } from '@/components/ui/Toast';
import { AuthProvider } from '@/components/providers/AuthProvider';
import { ThemeProvider } from '@/components/providers/ThemeProvider';

// ─── QueryClient config ───────────────────────────────────────────────────────
function makeQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        // Stale time: 30 seconds — feed data is fresh for 30s before background refetch
        staleTime: 30_000,
        // Cache time: 5 minutes
        gcTime: 5 * 60 * 1000,
        // Retry failed requests once (not on 4xx errors — see queryClient.ts)
        retry: (failureCount, error) => {
          // Never retry auth errors or not-found
          if (
            error instanceof Error &&
            'status' in error &&
            typeof (error as { status: number }).status === 'number'
          ) {
            const status = (error as { status: number }).status;
            if (status === 401 || status === 403 || status === 404) return false;
          }
          return failureCount < 1;
        },
        // Refetch when tab regains focus (keeps feed fresh)
        refetchOnWindowFocus: true,
      },
      mutations: {
        // Do not retry mutations — they may have side effects
        retry: false,
      },
    },
  });
}

interface AppProvidersProps {
  children: React.ReactNode;
}

export function AppProviders({ children }: AppProvidersProps) {
  // Create QueryClient once per component instance (not per render)
  // useState ensures it's stable across re-renders
  const [queryClient] = useState(() => makeQueryClient());

  return (
    <ThemeProvider
      attribute="class"
      defaultTheme="system"
      enableSystem
      disableTransitionOnChange
    >
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <ToastProvider>
            {children}
          </ToastProvider>
        </AuthProvider>
        {/* Dev tools only in development */}
        {process.env.NODE_ENV === 'development' && (
          <ReactQueryDevtools initialIsOpen={false} buttonPosition="bottom-left" />
        )}
      </QueryClientProvider>
    </ThemeProvider>
  );
}
