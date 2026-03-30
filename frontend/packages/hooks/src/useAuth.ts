// 📍 LOCATION: free-space/frontend/packages/hooks/src/useAuth.ts
//
// useAuth — convenience hook that reads from the Zustand auth store.
// Returns the current user and common auth actions.
// Components should use this hook rather than useAuthStore directly
// to keep store selection logic in one place.
//
// NOTE: This hook is web-only (uses the web authStore).
// Mobile has its own equivalent in apps/mobile/src/stores/authStore.ts

import { useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';

// Re-exported for convenience — components only need to import from hooks
export type { AuthenticatedUser } from '@qommunity/types';