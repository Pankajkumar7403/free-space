# Stage 2 Gap Audit (Post-Auth Stabilization)

**Date:** 2026-04-21  
**Scope:** Consolidated audit across backend milestones `M1..M7` and frontend milestones `FM1..FM8` after Stage 1 auth stabilization/hardening.

---

## Overall Readout

- Auth baseline is now operational on web with local host canonicalization and callback hardening in place.
- The codebase has broad implementation coverage, but many milestones are **partial** or **implemented-but-broken** due to integration contract drift and missing route surfaces.
- Highest leverage next step is to close **cross-service contract mismatches** and **user-facing dead-end routes** before adding new major features.

---

## Backend Matrix (M1..M7)

- `M1`: **working** — foundation/core infra is present and coherently tested.
- `M2`: **partial** — user/auth domain is substantial but event emission and some policy enforcement are incomplete.
- `M3`: **partial** — post/media exists, but media ownership/surface is fragmented.
- `M4`: **partial** — feed engine exists with tests, but upstream event dependencies are uneven.
- `M5`: **implemented but broken** — likes/comments exist, but wiring/policy consistency is weak.
- `M6`: **implemented but broken** — notifications/channels stack exists, but producer-consumer payload contracts drift.
- `M7`: **partial** — hardening/observability exists, but full launch-grade rollout integration is incomplete.

### Backend Critical Gaps

1. Notification producer/consumer Kafka payload contracts are inconsistent (`likes/comments/users` to notifications/feed).
2. `user.followed` event production path is effectively missing.
3. Media architecture is split between `apps/posts` and partially empty `apps/media`.
4. Notification endpoint naming drifts from expected/tested contracts.
5. Permission classes exist but are not consistently enforced in view paths.

---

## Frontend Matrix (FM1..FM8)

- `FM1`: **working** — monorepo/package/CI foundation is solid.
- `FM2`: **implemented but broken** — web auth is stabilized, but shared/mobile auth path is incomplete.
- `FM3`: **partial** — feed/post rendering is good; core post journey routes remain missing.
- `FM4`: **partial** — profile + follow core exists, but major social graph pages/settings flows are incomplete.
- `FM5`: **partial** — likes are implemented; comments/thread/moderation UI is largely missing.
- `FM6`: **not started** — no complete notification center / websocket event pipeline.
- `FM7`: **partial** — explore/hashtag pages exist; unified search/community spaces are missing.
- `FM8`: **partial** — unit tests/CI exist; E2E/observability/perf hardening is mostly absent.

### Frontend Critical Gaps

1. Navigation/protected routes point to missing pages (`/notifications`, `/create`, `/bookmarks`, `/p/[postId]`).
2. Mobile layout references non-existent screens (auth/main path graph inconsistency).
3. Comments/thread/reply moderation UX is not wired despite backend/API surface.
4. No real-time notification loop (socket manager + notification center).
5. Shared auth hook/package architecture remains incomplete for cross-platform consistency.

---

## Recommended Next Execution Slice (Single Slice)

### Slice Name
**Contract + Route Closure Mini-Slice**

### Why this slice now
It is the smallest high-impact slice that reduces breakage risk immediately across both backend and frontend, while preserving stage-gated execution discipline.

### Scope

1. **Backend (contract closure):**
   - unify event payload schema for `like.created`, `comment.created`, `user.followed`.
   - wire missing follow event emission.
   - add contract tests for producer -> consumer compatibility.

2. **Frontend (route closure):**
   - implement minimal `/(main)/p/[postId]` page.
   - resolve one or two highest-impact missing nav dead-ends (`/notifications` placeholder or `/create` placeholder as explicit non-broken route).
   - add focused tests for route existence/navigation.

### Out of scope
- Full FM6 websocket feature set.
- Full media refactor.
- Full mobile parity.

---

## Execution Order Recommendation

1. Backend event contract unification (stabilizes notification/feed dependencies).
2. Frontend post-detail + route dead-end closure.
3. Re-run cross-layer verification.
4. Start FM5 comment-thread slice only after the above passes.
