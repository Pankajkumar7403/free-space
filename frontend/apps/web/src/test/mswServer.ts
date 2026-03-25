// 📍 LOCATION: free-space/frontend/apps/web/src/test/mswServer.ts
//
// Mock Service Worker server for tests.
// All HTTP mocking goes through MSW — tests run fully offline.
// Add request handlers here or inline in individual test files with server.use().

import { setupServer } from 'msw/node';
import { authHandlers } from './handlers/authHandlers';
import { userHandlers } from './handlers/userHandlers';

// Default handlers — active in all tests
export const server = setupServer(
  ...authHandlers,
  ...userHandlers,
);
