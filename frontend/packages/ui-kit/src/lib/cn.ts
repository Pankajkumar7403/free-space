// 📍 LOCATION: free-space/frontend/packages/ui-kit/src/lib/cn.ts
//
// Shared cn() utility — merges Tailwind classes safely.
// Used by web components. Mobile uses StyleSheet.create() patterns instead.

import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
