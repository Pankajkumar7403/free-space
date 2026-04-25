# Auth Flow Stabilization and Stage-Gated Delivery Design

**Date:** 2026-04-21  
**Project:** Qommunity (Frontend + Backend)  
**Focus:** Make authentication flow reliably functional first, then execute roadmap features only after stage-level verification passes.

---

## 1) Problem Statement

The first user journey (authentication) is currently broken even though multiple roadmap modules have been partially implemented.

The verified immediate root cause is local environment host mismatch:

- Frontend auth proxy routes call `http://localhost:8000/api/v1`.
- Django backend for Qommunity is running on `http://127.0.0.1:8000`.
- Another service on `localhost:8000` responds with unrelated routes, producing 404 responses for auth endpoints.

Result: OAuth init and auth session flow fail before feature logic can be validated.

---

## 2) Goals

1. Restore a fully working web auth flow end-to-end as the first stable baseline.
2. Enforce a single canonical local host strategy (`127.0.0.1`) to avoid silent routing drift.
3. Introduce stage gates so roadmap progress only advances after previous stage is verified.
4. Create a repeatable process for learning + building: diagnose, fix, verify, then move to the next milestone block.

---

## 3) Non-Goals

- No large refactor of completed modules in this phase.
- No attempt to complete all roadmap gaps in one pass.
- No production deployment changes in this design step.

---

## 4) Design Overview

The delivery model is a staged pipeline:

1. **Stabilize Auth Baseline (M2/FM2 critical path).**
2. **Audit roadmap completion status vs working behavior.**
3. **Execute missing features in dependency order, one verified stage at a time.**

Each stage has explicit entry/exit criteria and verification commands.

---

## 5) Stage 1 Design: Auth Baseline Stabilization

### 5.1 Architecture/Configuration Decisions

- Canonical local backend base URL: `http://127.0.0.1:8000/api/v1`.
- Frontend auth API routes must consistently target that base URL in local development.
- OAuth redirect URI generation must remain deterministic and match provider registration behavior.
- Keep secure cookie strategy: refresh token in httpOnly cookie, access token in memory/session restore flow.

### 5.2 Components in Scope

- Web auth UI triggers:
  - `frontend/apps/web/src/components/features/auth/OAuthButtons.tsx`
- Next.js auth proxy routes:
  - `frontend/apps/web/src/app/api/auth/oauth/init/route.ts`
  - `frontend/apps/web/src/app/api/auth/oauth/callback/route.ts`
  - `frontend/apps/web/src/app/api/auth/session/route.ts`
  - `frontend/apps/web/src/app/api/auth/set-cookie/route.ts`
- Alias user routes that forward to auth routes (must stay aligned):
  - `frontend/apps/web/src/app/api/users/oauth/init/route.ts`
  - `frontend/apps/web/src/app/api/users/oauth/callback/route.ts`
  - `frontend/apps/web/src/app/api/users/session/route.ts`
  - `frontend/apps/web/src/app/api/users/set-cookie/route.ts`
- Env and docs alignment:
  - frontend env defaults/examples + README setup notes.

### 5.3 Data Flow (Expected Happy Path)

1. User taps Google/Apple in `OAuthButtons`.
2. Frontend requests `/api/auth/oauth/init`.
3. Next.js route calls Django `/api/v1/users/oauth/<provider>/init/`.
4. Backend returns provider URL with signed `state`.
5. User authenticates at provider; provider redirects to `/api/auth/oauth/callback`.
6. Callback route posts `code + state + redirect_uri` to backend OAuth callback endpoint.
7. Backend returns app token pair.
8. Next.js sets refresh cookie and redirects user to app route.
9. Session route exchanges refresh for access + fetches `/users/me/`.
10. App enters authenticated state.

### 5.4 Failure Handling Rules

- Missing provider/code/state -> deterministic redirect with auth error code.
- Backend non-200 response -> do not partially initialize session.
- Session refresh failure -> clear refresh cookie and return 401.
- Do not swallow host mismatch errors silently; make diagnostics obvious in logs and docs.

### 5.5 Verification Requirements (Stage 1 Exit Criteria)

Stage 1 is complete only if all pass:

- `GET /api/auth/oauth/init?provider=google...` returns `200` with URL payload.
- Login/register flow reaches authenticated UI state.
- Session restore works on page reload.
- Logout clears session and protected route access.
- Relevant auth tests pass (existing + any added smoke tests).

---

## 6) Stage 2 Design: Roadmap Gap Audit (Reality vs Planned)

After Stage 1 is green, produce a gap matrix by milestone:

- **Backend:** M1..M7 status per critical checklist item:
  - implemented + working
  - implemented but broken
  - partial
  - not started
- **Frontend:** FM1..FM8 status with same labels.

Output must include dependency notes and blockers, not just completion percentages.

Exit criteria:

- Prioritized backlog ordered by dependency and user impact.
- Clear next stage candidate with bounded scope.

---

## 7) Stage 3 Design: Sequential Stage Execution Model

For each next stage:

1. Define scope (small, dependency-safe slice).
2. Write/confirm failing test or reproducible check.
3. Implement minimal changes.
4. Run verification (tests + manual path checks).
5. Mark stage complete only on green results.
6. Move to next stage.

Rule: no new stage starts with unresolved failures from previous stage.

---

## 8) Testing Strategy for This Design

- Use existing test stack first (Vitest for web, pytest for backend).
- Add focused smoke tests for auth critical path where gaps exist.
- Prefer deterministic API route checks (status + response shape + cookie behavior).
- Keep tests offline and reproducible in local dev.

---

## 9) Risks and Mitigations

- **Risk:** Local host drift returns in new files.
  - **Mitigation:** single canonical env values + setup docs + quick startup check.
- **Risk:** Partial auth fixes hide deeper state issues.
  - **Mitigation:** verify full flow (init, callback, set-cookie, session restore, logout), not one endpoint.
- **Risk:** Feature creep before baseline stability.
  - **Mitigation:** enforce stage gate exit criteria before roadmap advancement.

---

## 10) Recommended Next Action

Proceed with Stage 1 implementation using canonical local host (`127.0.0.1`) and complete auth baseline verification before auditing later milestones.
