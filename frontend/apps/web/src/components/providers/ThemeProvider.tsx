// 📍 LOCATION: free-space/frontend/apps/web/src/components/providers/ThemeProvider.tsx
//
// Thin wrapper around next-themes to satisfy the 'use client' requirement
// while keeping it importable from the server-component AppProviders.

'use client';

import { ThemeProvider as NextThemesProvider } from 'next-themes';
import type { ThemeProviderProps } from 'next-themes';

export function ThemeProvider({ children, ...props }: ThemeProviderProps) {
  return <NextThemesProvider {...props}>{children}</NextThemesProvider>;
}
