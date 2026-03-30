// 📍 LOCATION: free-space/frontend/apps/web/src/lib/env.ts
//
// Type-safe environment variables using @t3-oss/env-nextjs.
// App will THROW at build time if required env vars are missing.
// Never access process.env directly — always import from here.

import { createEnv } from '@t3-oss/env-nextjs';
import { z } from 'zod';

export const env = createEnv({
  /**
   * Server-side env vars — NEVER sent to browser.
   * Available in: Server Components, API routes, middleware.
   */
  server: {
    // NextAuth
    AUTH_SECRET: z.string().min(32, 'AUTH_SECRET must be at least 32 characters'),

    // Internal API URL (server → backend, not via CDN)
    API_INTERNAL_URL: z.string().url().default('http://localhost:8000/api/v1'),

    // Node env
    NODE_ENV: z.enum(['development', 'test', 'production']).default('development'),
  },

  /**
   * Client-side env vars — NEXT_PUBLIC_ prefix, safe to expose.
   * Available everywhere.
   */
  client: {
    // Django REST API base URL (via Nginx in production)
    NEXT_PUBLIC_API_URL: z.string().url().default('http://localhost:8000/api/v1'),

    // WebSocket URL (Django Channels)
    NEXT_PUBLIC_WS_URL: z.string().default('ws://localhost:8000/ws'),

    // App URL
    NEXT_PUBLIC_APP_URL: z.string().url().default('http://localhost:3000'),

    // Sentry (optional — only in production)
    NEXT_PUBLIC_SENTRY_DSN: z.string().url().optional(),

    // PostHog analytics (opt-in)
    NEXT_PUBLIC_POSTHOG_KEY: z.string().optional(),
    NEXT_PUBLIC_POSTHOG_HOST: z.string().url().optional(),
  },

  /**
   * For Next.js >= 13.4, destructure from process.env manually.
   * This prevents accidental server-side env leaks.
   */
  runtimeEnv: {
    // Server
    AUTH_SECRET:          process.env.AUTH_SECRET,
    API_INTERNAL_URL:     process.env.API_INTERNAL_URL,
    NODE_ENV:             process.env.NODE_ENV,
    // Client
    NEXT_PUBLIC_API_URL:      process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_WS_URL:       process.env.NEXT_PUBLIC_WS_URL,
    NEXT_PUBLIC_APP_URL:      process.env.NEXT_PUBLIC_APP_URL,
    NEXT_PUBLIC_SENTRY_DSN:   process.env.NEXT_PUBLIC_SENTRY_DSN,
    NEXT_PUBLIC_POSTHOG_KEY:  process.env.NEXT_PUBLIC_POSTHOG_KEY,
    NEXT_PUBLIC_POSTHOG_HOST: process.env.NEXT_PUBLIC_POSTHOG_HOST,
  },

  // Skip validation in CI when building without all env vars
  skipValidation: process.env.SKIP_ENV_VALIDATION === 'true',
});
