// 📍 LOCATION: free-space/frontend/apps/web/vitest.config.ts

import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    // jsdom simulates the browser DOM for React component tests
    environment: 'jsdom',

    // Run setup file before each test — imports jest-dom matchers
    setupFiles: ['./src/test/setup.ts'],

    // Glob patterns for test files
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    exclude: ['node_modules', '.next', 'e2e'],

    // Coverage
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      include: ['src/**/*.{ts,tsx}'],
      exclude: [
        'src/test/**',
        'src/app/**',          // Pages are thin — tested via E2E
        'src/**/*.stories.tsx',
        'src/**/index.ts',
        '**/*.d.ts',
      ],
      thresholds: {
        // Enforce minimum coverage — fail CI if below these
        lines:     80,
        functions: 80,
        branches:  75,
        statements:80,
      },
    },

    // Alias resolution — matches tsconfig paths
    alias: {
      '@': resolve(__dirname, './src'),
    },

    // Global test utilities (describe, it, expect) — no import needed
    globals: true,
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
      '@qommunity/types':      resolve(__dirname, '../../packages/types/src/index.ts'),
      '@qommunity/api-client': resolve(__dirname, '../../packages/api-client/src/index.ts'),
      '@qommunity/validators': resolve(__dirname, '../../packages/validators/src/index.ts'),
      '@qommunity/hooks': resolve(__dirname, '../../packages/hooks/src/index.ts'),
    },
  },
});