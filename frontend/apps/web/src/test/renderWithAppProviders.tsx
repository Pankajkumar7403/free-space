// 📍 LOCATION: free-space/frontend/apps/web/src/test/renderWithAppProviders.tsx
//
// Shared test wrapper: QueryClient + ToastProvider (matches common component deps).

import type { ReactElement } from 'react';
import { render, type RenderResult } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ToastProvider } from '@/components/ui/Toast';

export function renderWithAppProviders(
  ui: ReactElement,
  options?: { queryClient?: QueryClient },
): RenderResult {
  const queryClient =
    options?.queryClient ??
    new QueryClient({
      defaultOptions: {
        mutations: { retry: false },
        queries: { retry: false },
      },
    });

  return render(
    <QueryClientProvider client={queryClient}>
      <ToastProvider>{ui}</ToastProvider>
    </QueryClientProvider>,
  );
}
