# 📍 LOCATION: free-space/frontend/README.md
# Qommunity — Frontend Monorepo

> 🏳️‍🌈 Built with pride. Engineered for safety.

## Project Structure

```
free-space/
├── backend/                    # Django REST API (existing)
└── frontend/                   # This monorepo
    ├── apps/
    │   ├── web/                # Next.js 15 App Router
    │   └── mobile/             # Expo 51 + React Native
    └── packages/
        ├── types/              # Shared TypeScript interfaces
        ├── api-client/         # Axios + JWT interceptor
        ├── validators/         # Zod schemas (mirror backend validators.py)
        ├── ui-kit/             # Design system (Sprint 3)
        ├── hooks/              # Shared React hooks (Sprint 3+)
        └── config/             # ESLint, tsconfig, Tailwind base configs
```

## Prerequisites

| Tool    | Version  | Install                          |
|---------|----------|----------------------------------|
| Node.js | ≥ 20.0   | https://nodejs.org               |
| pnpm    | ≥ 9.0    | `npm install -g pnpm@9`          |
| Expo CLI| latest   | `npm install -g expo-cli`        |
| EAS CLI | latest   | `npm install -g eas-cli`         |

---

## ⚡ Full Setup Command (run once from `free-space/`)

```bash
# ── 1. Create the frontend directory alongside backend ──────────────────────
mkdir -p frontend

# ── 2. Create full directory tree ────────────────────────────────────────────
mkdir -p frontend/{.github/workflows,apps/{web/src/{app/{api/auth/{set-cookie,session,logout},'(auth)'/{login,register},'(main)'},components/{ui,features/{auth,navigation},providers},lib,stores,test/{handlers}},mobile/{app/{'(auth)','(main)'},src/{lib,stores}}},packages/{types/src/__tests__,api-client/src/endpoints,validators/src/__tests__,config/{tsconfig,eslint,tailwind},ui-kit/src,hooks/src,test-utils/src}}

# ── 3. Copy all generated files into place ───────────────────────────────────
# (files are created by Claude — paste each file at its 📍 LOCATION path)

# ── 4. Install all dependencies ──────────────────────────────────────────────
cd frontend
pnpm install

# ── 5. Set up environment variables ─────────────────────────────────────────
cp apps/web/.env.example    apps/web/.env.local
cp apps/mobile/.env.example apps/mobile/.env
# Then edit both files with your actual values

# ── 6. Set up Husky git hooks ────────────────────────────────────────────────
pnpm exec husky install

# ── 7. Verify everything works ───────────────────────────────────────────────
pnpm type-check
pnpm lint
pnpm test
```

---

## Development

```bash
# Start both web + mobile dev servers
pnpm dev

# Web only (http://localhost:3000)
pnpm dev:web

# Mobile only (Expo Go)
pnpm dev:mobile

# Run tests (all packages)
pnpm test

# Run tests with coverage
pnpm test:coverage

# Type check all packages
pnpm type-check

# Lint + format check
pnpm lint
pnpm format:check

# Fix linting issues
pnpm lint:fix

# Fix formatting
pnpm format
```

---

## Sprint Status

| Sprint | Focus                        | Status        |
|--------|------------------------------|---------------|
| S1     | Monorepo Bootstrap           | ✅ Complete   |
| S2     | Shared Package Core          | ✅ Complete   |
| S3     | Design System Foundation     | 🟡 Next       |
| S4     | Auth UI (web + mobile)       | ✅ Complete   |
| S5     | Feed Shell                   | 🔵 Planned    |
| S6     | PostCard & Feed List         | 🔵 Planned    |
| ...    | ...                          | 🔵 Planned    |

---

## 📍 File Location Convention

Every file generated in this project has a `📍 LOCATION:` comment at the top.
This is the canonical path relative to `free-space/`. When pasting files, use
this comment as the source of truth for where the file belongs.

**Example:**
```ts
// 📍 LOCATION: free-space/frontend/packages/types/src/user.ts
```
→ Paste at `free-space/frontend/packages/types/src/user.ts`

---

## Architecture Decisions

- **Tokens**: Access token in memory only. Refresh token in httpOnly cookie (web) / SecureStore (mobile). Never in localStorage.
- **Error handling**: All errors normalised to `ApiException` via Axios interceptor. Components never parse raw error strings.
- **Validation**: Zod schemas in `packages/validators` mirror backend `validators.py`. One source of truth.
- **State**: TanStack Query for server state. Zustand for client state (auth, UI). No prop drilling beyond 2 levels.
- **Testing**: MSW mocks all HTTP. Tests run fully offline. No real network in unit/integration tests.
