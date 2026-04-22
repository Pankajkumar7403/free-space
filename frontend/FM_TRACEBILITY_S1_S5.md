# FM / Sprint 1–5 Traceability Matrix

Source of truth: roadmap FM deliverables (S1–S5) mapped to repository artifacts. Use this for compliance reviews and regressions.

| Sprint | FM / deliverable theme | Code / contract artifacts | Compliance |
|--------|------------------------|---------------------------|------------|
| S1 | Monorepo bootstrap (Turborepo, apps, packages, scripts) | [`package.json`](package.json), [`pnpm-workspace.yaml`](pnpm-workspace.yaml), [`turbo.json`](turbo.json), `apps/web`, `apps/mobile`, `packages/*` | OK |
| S2 | Shared core (types, validators, api-client, hooks) | [`packages/types`](packages/types), [`packages/validators`](packages/validators), [`packages/api-client`](packages/api-client), [`packages/hooks`](packages/hooks), [`queryKeys.ts`](packages/hooks/src/queryKeys.ts) | OK — keys centralized; feed uses [`FeedPage`](packages/types/src/feed.ts) + `next_cursor` |
| S3 | Design system (tokens, primitives) | [`packages/ui-kit`](packages/ui-kit) primitives export | OK |
| S4 | Auth UI + session semantics | `apps/web/src/app/(auth)`, [`authStore`](apps/web/src/stores/authStore.ts), Next API auth routes under `app/api/auth`, [`OAuthButtons`](apps/web/src/components/features/auth/OAuthButtons.tsx) | OK after OAuth redirect uses [`env.NEXT_PUBLIC_API_URL`](apps/web/src/lib/env.ts) (not relative `/api/v1`) |
| S5 | Feed shell (layout, providers, home feed) | [`(main)/layout.tsx`](apps/web/src/app/(main)/layout.tsx), [`AppProviders`](apps/web/src/components/providers/AppProviders.tsx), [`feed/page.tsx`](apps/web/src/app/(main)/feed/page.tsx), [`FeedList`](apps/web/src/components/features/feed/FeedList.tsx), [`PostCard`](apps/web/src/components/features/feed/PostCard.tsx) | OK |

## Gap classification (resolved / watch)

| Severity | Issue | Resolution |
|----------|-------|------------|
| Critical | OAuth initiation used relative `/api/v1/...` (Next has no proxy) | Fixed: full backend base from `env.NEXT_PUBLIC_API_URL` |
| High | Like optimistic update only touched `feed.home` cache | Fixed: `setQueriesData` / invalidate under `['feed']` prefix |
| High | Bookmark control had no mutation | Fixed: `useBookmarkPost` + PostCard wiring |
| Medium | Nav linked to `/explore`, `/hashtag/...` without pages | Fixed: explore + hashtag routes + shared feed view |
| Medium | `useFeed.ts` header comment referenced legacy `next` cursor | Fixed: documentation matches `next_cursor` |

## Sprint 6 (PostCard & feed surfaces) — baseline

| Deliverable | Artifacts |
|-------------|-----------|
| PostCard + actions | [`PostCard.tsx`](apps/web/src/components/features/feed/PostCard.tsx), tests in [`PostCard.test.tsx`](apps/web/src/components/features/feed/__tests__/PostCard.test.tsx) |
| Home feed list | [`feed/page.tsx`](apps/web/src/app/(main)/feed/page.tsx), [`FeedList`](apps/web/src/components/features/feed/FeedList.tsx) |
| Explore + trending | [`explore/page.tsx`](apps/web/src/app/(main)/explore/page.tsx), [`explore/trending/page.tsx`](apps/web/src/app/(main)/explore/trending/page.tsx) |
| Hashtag feed | [`hashtag/[tag]/page.tsx`](apps/web/src/app/(main)/hashtag/[tag]/page.tsx), `HashtagFeedList`, backend `/feed/hashtag/{tag}/` |
| Bookmark mutation | [`useBookmarkPost`](packages/hooks/src/usePost.ts) |

## Conventions checklist (S1–S5)

- Server state: TanStack Query; keys from `queryKeys` only — **yes**
- API I/O: `@qommunity/api-client` — **yes** (logout via Next route is intentional for cookie)
- Auth tokens: access in memory / refresh httpOnly — **yes** (web)
- Zod in `packages/validators` for forms — **yes** (auth forms)
