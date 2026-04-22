# Frontend FM Audit (Sprint 1-5)

This audit maps the current codebase to the roadmap FM/Sprint deliverables for S1-S5.

**Formal traceability matrix:** see [FM_TRACEBILITY_S1_S5.md](./FM_TRACEBILITY_S1_S5.md).

## Sprint 1 - Monorepo Bootstrap

- **Status:** aligned
- **Evidence:** `frontend/package.json`, `frontend/pnpm-workspace.yaml`, `frontend/turbo.json`, `frontend/apps/web`, `frontend/apps/mobile`, `frontend/packages/*`
- **Notes:** CI/lint/type/test/build scripts are present and workspace package layout matches roadmap.

## Sprint 2 - Shared Package Core

- **Status:** mostly aligned
- **Evidence:** `frontend/packages/types`, `frontend/packages/validators`, `frontend/packages/api-client`
- **Gaps fixed in this alignment:**
  - Feed contract drift resolved:
    - `packages/types/src/feed.ts` now matches backend response (`results`, `next_cursor`, `source`)
    - `packages/hooks/src/useFeed.ts` cursor handling now uses `next_cursor`
    - `apps/web/src/components/features/feed/FeedList.tsx` now consumes `Post[]` shape correctly

## Sprint 3 - Design System Foundation

- **Status:** aligned after refactor
- **Evidence:** `frontend/packages/ui-kit/src/tokens/*`, `frontend/packages/ui-kit/src/primitives/*`
- **Gaps fixed in this alignment:**
  - Added missing core primitives required by roadmap FM deliverables:
    - `Button`, `Input`, `Avatar`, `Skeleton`, `Spinner`, `Toast`
  - Updated central primitive exports in `packages/ui-kit/src/primitives/index.ts`

## Sprint 4 - Auth UI

- **Status:** mostly aligned
- **Evidence:** auth routes/pages/components under `apps/web/src/app/(auth)` and `apps/mobile/app/(auth)`, auth store in `apps/web/src/stores/authStore.ts`
- **Gaps fixed in this alignment:**
  - OAuth URL naming corrected in `apps/web/src/components/features/auth/OAuthButtons.tsx`:
    - `/api/v1/users/auth/oauth/...` -> `/api/v1/users/oauth/...`

## Sprint 5 - Feed Shell

- **Status:** aligned after refactor
- **Evidence:** `apps/web/src/app/(main)/layout.tsx`, query provider in `apps/web/src/components/providers/AppProviders.tsx`, feed components in `apps/web/src/components/features/feed/*`
- **Gaps fixed in this alignment:**
  - Replaced placeholder feed page with working shell in:
    - `apps/web/src/app/(main)/feed/page.tsx`
  - Page now renders `FeedList` with loading/error/empty states.

## Priority Gap Summary

- **Critical fixed:** Feed API response contract mismatch (`next` vs `next_cursor`, nested item shape mismatch)
- **High fixed:** OAuth initiation used relative `/api/v1/...` instead of `env.NEXT_PUBLIC_API_URL` (browser 404)
- **High fixed:** Like/bookmark cache + tests — feed mutations now merge API results; tests use `FeedCachedPostCard` harness
- **High fixed:** Follow optimistic UI — `FollowButton` reads `useQuery(profile)`; follow/unfollow no longer invalidate profile into stale MSW
- **Medium fixed:** Sprint status documentation drift in `frontend/README.md`
- **Medium fixed:** Vitest setup path (`src/test/setup.ts`), MSW auth paths (`/users/login/`), and `configureApiClient` in test setup
