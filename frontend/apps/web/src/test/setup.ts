// 📍 LOCATION: free-space/frontend/apps/web/src/tests/setup.ts
//
// Runs before every test file.
// Sets up:
//  - jest-dom matchers (toBeInTheDocument, toHaveValue, etc.)
//  - MSW server (starts/resets/stops between tests)
//  - Global fetch mock (Next.js compatibility)
//  - window.matchMedia stub (Tailwind responsive hooks)

import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import { afterAll, afterEach, beforeAll, vi } from 'vitest';
import { server } from './mocks/server';

// ─── MSW server lifecycle ─────────────────────────────────────────────────────
beforeAll(() => server.listen({ onUnhandledRequest: 'warn' }));
afterEach(() => {
  server.resetHandlers();  // Reset per-test overrides
  cleanup();               // Unmount React components
});
afterAll(() => server.close());

// ─── window.matchMedia stub ───────────────────────────────────────────────────
// jsdom doesn't implement matchMedia — stub it so Tailwind hooks don't throw
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// ─── IntersectionObserver stub ───────────────────────────────────────────────
// Needed by infinite scroll / virtualized list components
class IntersectionObserverMock {
  observe    = vi.fn();
  disconnect = vi.fn();
  unobserve  = vi.fn();
}
Object.defineProperty(window, 'IntersectionObserver', {
  writable: true,
  configurable: true,
  value: IntersectionObserverMock,
});

// ─── ResizeObserver stub ──────────────────────────────────────────────────────
class ResizeObserverMock {
  observe    = vi.fn();
  disconnect = vi.fn();
  unobserve  = vi.fn();
}
Object.defineProperty(window, 'ResizeObserver', {
  writable: true,
  configurable: true,
  value: ResizeObserverMock,
});

// ─── Next.js router mock ──────────────────────────────────────────────────────
vi.mock('next/navigation', () => ({
  useRouter:      vi.fn(() => ({ push: vi.fn(), replace: vi.fn(), refresh: vi.fn() })),
  useSearchParams:vi.fn(() => ({ get: vi.fn(() => null) })),
  usePathname:    vi.fn(() => '/'),
  redirect:       vi.fn(),
}));
