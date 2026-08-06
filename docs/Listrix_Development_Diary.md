# Listrix — Development Diary (Living Document)

> A running log of design decisions, architecture changes, feature additions, critiques,
> recommendations, and roadmap. Append new entries at the top of "Timeline". Keep it honest —
> record trade-offs and what is simulated vs real.

---

## How to use this diary
- Add an entry whenever you make a meaningful decision, add/complete a feature, fix a notable bug,
  or change architecture.
- Each entry: **date/session · what changed · why · impact · follow-ups**.
- Cross-reference `/app/docs/HANDOVER.md` sections for depth and `/app/plan.md` for phase status.

---

## Project snapshot (current)
- **Product:** multi-tenant AI Business OS for resellers (FARM stack; OpenAI-compatible LLM via `LLM_API_KEY`).
- **Foundation:** multi-business workspaces with verified 100% data isolation.
- **Auth:** implemented backend-first, staged (`AUTH_REQUIRED=false` keeps the no-auth preview working).
- **Integrations/market signals:** TradeMe real (OAuth 1.0a, staged); other connectors simulated.
- **Backend:** modular — `server.py` is the app factory; domain logic in `routes/` + `services/` +
  `models/` + `db/`.
- **Financials:** `GET /api/financials` — realized (sold) vs potential (open) P&L; sales tracked
  via `mark-sold`/`mark-unsold`.
- **Platform:** object storage + thumbnails, background jobs, notifications, opt-in scheduler,
  Facebook/Gmail adapters (staged), item lifecycle stages, global search, CSV import, analytics,
  members/roles.

---

## Timeline (newest first)
### Session — Command Center polish (Dashboard chart + inventory table)
**What changed**
- **Activity Overview chart:** a large full-width area chart now sits directly under the KPI row,
  matching the owner's reference image. Fed by real event analytics (`GET /api/analytics` →
  `events_by_day`), with a safe fallback that derives per-day counts from the event stream when
  analytics has no rows, so the dashboard never crashes on empty data.
- **Inventory Snapshot table:** full-width data table below the chart with Item / Condition /
  Est. Value / AI Confidence / Status columns. Rows are clickable through to the item detail page,
  mirroring the existing ItemCard navigation; thumbnails, condition score bars, AI confidence
  chips and Sold/Listed/Draft badges reuse the app's existing derived metrics
  (`estimatedValue`, `conditionScore`, `confidenceFor`).
- New components: `frontend/src/components/DashboardChart.js`, `frontend/src/components/DashboardTable.js`;
  both wired into `frontend/src/pages/Dashboard.js` without touching any existing sections.
- Production build validated (esbuild clean, `yarn build` succeeds) and served as the stable local preview.

**Why**
- Owner requested: "The UI needs to be in the same layout and style as the image upload" (KPI cards →
  large chart → data table, all in the dark industrial card style).

**Impact**
- Dashboard now reads top-down like the reference: briefing → KPIs → chart → table → actions,
  with the existing intelligence widgets and event stream preserved.

**Follow-ups (not yet done)**
- Chart/table remain data-driven from real items/events; add a time-range selector and
  marketplace-split series when TradeMe/Facebook sync produce multi-channel volume.

## Timeline (newest first)

### Session — Connection Wizard (live integration setup in-app)
**What changed**
- **In-app Connection Wizard:** the Integration Hub now lets a non-technical owner paste, test,
  save, and disconnect live credentials for TradeMe, Facebook Marketplace and Gmail — no server
  files or environment editing needed. Credentials are encrypted at rest per workspace
  (`integrations.setup`, Fernet) and never returned to the client.
- New endpoints: `POST /integrations/{platform}/config`, `POST /integrations/{platform}/test`
  (live connectivity check against the real provider), `POST /integrations/{platform}/disconnect`,
  `GET /integrations/status` (per-connector mode live/simulated, configured, last test result).
- Adapters resolve credentials stored-first, environment fallback (`services/integrations/creds.py`);
  TradeMe OAuth guard now accepts wizard-saved consumer keys; Callback URL is optional.
- Frontend `IntegrationHub.js` rebuilt as a step-by-step wizard (get keys → paste → test → save &
  connect) with live/simulated status badges; legacy simulated toggle preserved for non-live
  connectors.

**Why**
- Owner request: "ensure a connection wizard or easy integration flow is working for live connections."

**Impact**
- Backend suite **88 passed / 3 skipped**; 6 new wizard tests added; full production frontend build
  succeeds (`yarn build`) and is served as the stable local preview.

**Follow-ups (not yet done)**
- Real TradeMe/Facebook/Gmail credentials still come from the owner's own accounts — the wizard
  walks them through it once those accounts exist.
- Gmail OAuth flow is token-paste based; a full Google OAuth redirect flow can replace it later.

## Timeline (newest first)

### Session — Emergent removal + Builder packaging (Owner handoff prep)
**What changed**
- **AI provider swap:** `backend/services/llm.py` rewritten onto the public `openai` SDK
  (`AsyncOpenAI`) with any OpenAI-compatible endpoint. Emergent is fully removed — no imports, no
  packages, no docs references. Config: `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL`
  (default `gpt-4o-mini`). Works with free tiers (Groq, OpenRouter) or local Ollama; core features
  run fine without a key (AI features skip gracefully).
- **Builder packaging:** PWA shell added (`manifest.json`, `sw.js`, 192/512 icons, SW registration
  in `src/index.js`), `capacitor.config.json` (appId `com.listrix.app`) so a developer can wrap the
  web app into an Android APK, and `docs/BUILDER_BRIEF.md` — a plain-language handoff for a
  non-technical owner (run instructions, free hosting, free AI options, APK path, pre-ship checklist).
- Frontend rebranded (title/theme/icons), Sidebar footer → "AI engine · online", all Emergent
  references scrubbed from source, configs, tests and docs.

**Why**
- Owner directive: "remove emergent and replace with free alternative" and deliver something a
  builder can turn into an APK — the owner is the creator, not a developer.

**Impact**
- Backend full suite still **83 passed / 3 skipped** (LLM tests skip without `LLM_API_KEY`);
  all 84 frontend source files esbuild-clean; docs verified free of Emergent references.

**Follow-ups (not yet done)**
- A developer must run `yarn install && yarn build`, then `npx cap add android` + Android Studio
  to produce the actual APK (or deploy the PWA and "Add to Home Screen" on a phone).
- Connect a real free LLM key (`LLM_API_KEY` + `LLM_BASE_URL`) before enabling AI features live.


### Session — Month 4–6 Sweep: Storage, Jobs, Connectors, Workflow, Scale (P1–P2, Phases 16–21)
**What changed**
- **Object storage (16):** `services/storage.py` + `image_blobs` collection; `POST /items/{id}/image`
  stores blobs + Pillow thumbnails out-of-line; `GET /images/{id}?thumb=1` serves bytes; items keep
  a tiny `image_id`. Frontend `imageSrc()` renders thumbs on cards/detail/kanban.
- **Jobs/notifications/scheduler (17):** `analyze-all` is now a persisted, pollable job
  (`GET /jobs/{id}`, concurrency 3); in-app notifications (`sale`, `stage`, …) with a header bell;
  opt-in `SCHEDULER_ENABLED` tick that enqueues analysis per workspace.
- **Real connectors + comms hub (18):** Facebook (Graph API page token) queues approval-gated
  price suggestions from Marketplace anchors; Gmail pulls buyer messages into the inbox; replies
  are drafts only. Both staged behind env tokens — unconfigured keeps the legacy toggle.
- **Workflow engine (19):** item `stage` lifecycle with validated transitions + Kanban/Timeline tabs.
- **Scale (20–21):** global search (`/api/search`), CSV import (`/workspaces/import`), event
  analytics (`/api/analytics`), workspace members/roles (owner-gated).

**Why**
- Owner directive to complete the remaining roadmap: images were bloating item docs; heavy calls
  blocked the event loop; buyer comms and multi-user collaboration were the last UX gaps.

**Impact**
- 17 new backend tests (11 platform + 6 connectors/roles). Full local suite
  **83 passed / 2 skipped** (`test_reports/iteration_10.json`); esbuild clean for all touched FE
  files. Docs updated: plan.md Phases 16–21, PROJECT_STATE, HANDOVER roadmap, this diary.

**Follow-ups (not yet done)**
- Live end-to-end validation of TradeMe/Facebook/Gmail with real credentials.
- Sales P&L refinements: per-sale COGS, payout reconciliation.
- Push/email notification channels; S3 swap for `image_blobs`; shared rate-limit store.

### Session — Sales Tracking → Realized P&L (P1, Phase 15b)
**What changed**
- `models/item.py` gains `sold`, `sold_at`, `sale_price`; `routes/items.py` adds
  `POST /items/{id}/mark-sold` (validates sale_price >= 0, 404 cross-workspace, optional sold_at)
  and `POST /items/{id}/mark-unsold` (revert); `ITEM_SOLD`/`ITEM_UNSOLD` event types logged.
- `services/financials.py` splits the books: sold items use `sale_price` → **realized** totals
  (revenue, gross, fees, tax, net, margin) while open items stay **potential**; combined
  `net_profit`/`net_margin_pct`; per-row `status` + `sale_price`; per-category `sold` counts.
- Frontend: Item Detail "Mark Sold" flow (inline sale-price input + confirm + revert), ItemCard
  "Sold · price" chip, Financials page realized/potential stat cards + Status column.

**Why**
- Financials showed only potential figures; recording real sales is the difference between
  "what could happen" and "what actually happened" — the core of resale P&L.

**Impact**
- 4 new backend tests (endpoint + event, validation/isolation, revert, realized-vs-potential math).
  Full local suite **66 passed / 2 skipped** (`test_reports/iteration_9.json`); esbuild clean.

**Follow-ups (not yet done)**
- Object storage for base64 images; background queue for `analyze-all`.

### Session — Financials (P1, Phase 15)
**What changed**
- `services/financials.py` + `GET /api/financials` (workspace-scoped): per-item rows (cost, price
  from listing → fallback `value_estimate.mid`, gross, 7.9% marketplace fee, tax from workspace
  `tax_rate`, net, margin_pct), totals (invested, potential revenue, net profit, net margin), and
  `by_category` aggregation. Items without both cost and price are skipped.
- Honest labeling: since sales are not tracked yet, every figure is returned as a **potential**
  figure and the response carries a `note` saying so.
- Frontend: `getFinancials`/`useFinancials`, new `Financials` page (totals cards, category table,
  top-items table, currency-aware money formatting), wired into Sidebar, AppShell and routes.

**Why**
- Month-4 roadmap item; resellers need to see margin per item/category before acting on AI
  pricing suggestions. Uses data already captured (cost, tax_rate, currency, listing price).

**Impact**
- 4 new backend tests (exact math, value-estimate fallback, workspace isolation, currency
  passthrough + 0% default tax, skip-no-numbers). Full local suite **62 passed / 2 skipped**
  (`test_reports/iteration_8.json`); esbuild syntax-check clean for all touched FE files.

**Follow-ups (not yet done)**
- Sales tracking (mark item sold + sale price) to convert potential P&L into realized P&L.
- Object storage for base64 images; background queue for `analyze-all`.

### Session — Real TradeMe Connector (P1, staged)
**What changed**
- `services/integrations/trademe.py`: real TradeMe adapter behind the existing connect/sync
  endpoints — OAuth 1.0a 3-legged flow (request token → authorize URL → verifier callback),
  live sync of the seller's current listings + market anchors, and pending (approval-gated)
  `reduce_price` suggestions with `params.new_price`. Never posts or mutates listings.
- Encrypted token storage at rest (Fernet via `cryptography`; `CONNECTOR_ENCRYPTION_KEY`, dev
  fallback derived from `JWT_SECRET`); `GET /integrations` excludes `tokens`/`config`.
- New `POST /api/integrations/{platform}/oauth/callback`; adapter registry with staged dispatch:
  without `TRADEME_CONSUMER_KEY/SECRET` the legacy simulated toggle/sync is preserved so the
  preview and the isolation suite keep working.
- Frontend: IntegrationHub opens the TradeMe authorize URL, handles the OAuth callback redirect
  (submits the verifier to the backend), and updates connector copy.
- Network calls run via `asyncio.to_thread`; adapter helpers are patchable for tests.

**Why**
- Handover §35 #10 / plan Phase 14: wire the first real marketplace with production-safe
  patterns (encrypted credentials + approval gate) before scaling to more connectors.

**Impact**
- 6 new tests: OAuth connect/callback, encrypted at-rest tokens, sync → pending suggestions with
  no listing mutation, idempotent re-sync, search fallback, threshold skip, legacy preservation.
  Full local suite 58 passed / 2 skipped (`test_reports/iteration_7.json`); live uvicorn smoke
  test of the legacy path + no-secret-leak on the list endpoint passed.

**Follow-ups (not yet done)**
- Live end-to-end validation with real TradeMe credentials + registered callback URL.
- Remaining roadmap: financials/object storage for images, background queue for `analyze-all`,
  communications hub, workflow engine, global search + notifications + roles.

### Session — Authentication & Authorization (P0, staged rollout)
**What changed**
- Added `users` collection and auth routes (`POST /api/auth/register`, `POST /api/auth/login`,
  `GET /api/auth/me`) with bcrypt password hashing and HS256 JWTs (`services/auth.py`). New
  `routes/auth.py`; `users` index added to `db/indexes.py`.
- Workspaces now carry `owner_id`; registration creates an owned default workspace (with seeded
  connectors); `/workspaces/{id}` GET/PUT/export are ownership-guarded (403 for other users).
- `get_wid` is auth-aware: an authenticated user's `X-Workspace-Id` is validated against ownership
  (403 on foreign workspaces), and missing headers fall back to the user's own default workspace.
- LLM endpoints are rate-limited per workspace (in-process sliding window, default 30/min) — 429
  when exceeded (`services/ratelimit.py`).
- **Staged enforcement**: `AUTH_REQUIRED` env (default `false`) keeps the no-auth preview working;
  `AUTH_REQUIRED=true` locks every `/api` route behind a JWT. Invalid/expired tokens always 401.
- Frontend: Bearer-token axios interceptor, `AuthContext` (login/register/logout/hydrate), `/login`
  page (sign in / create account), and a header Sign in/out control. All screens still work without
  auth in grace mode.

**Why**
- Handover §25 / plan Phase 13: the top production blocker before real multi-user exposure.

**Impact**
- 12 new auth tests; full local suite now 52 passed / 2 skipped; live uvicorn smoke tests in both
  grace and strict modes passed (`test_reports/iteration_6.json`).
- Workspace isolation now composes with identity: no cross-user reads/writes, and tenancy is
  derived from the session, not trusted from the client alone.

**Follow-ups (not yet done)**
- Frontend polish for the login flow + gate the app when `AUTH_REQUIRED=true` (deploy flag first).
- Per-workspace usage quotas/budgets; CORS lockdown for multi-origin; token refresh/rotation.
- Real TradeMe connector; object storage for images; background queue for `analyze-all`.

### Session — Backend Modularization, Indexes & LLM Resilience
**What changed**
- Refactored the monolithic `backend/server.py` (~1000 lines) into a modular layout with **zero behavior
  change** (route parity verified: 33/33 identical paths/methods):
  - `config.py` (constants/env), `deps.py` (Mongo handle + `get_wid`), `utils.py` (pure helpers)
  - `db/` → `migrations.py` (default workspace + legacy backfill), `indexes.py` (ensure_indexes)
  - `models/` → Pydantic models grouped by domain (workspace, item, event, agent, ai)
  - `services/` → `events.py` (typed `EventType` enum + audit logging), `llm.py` (shared LLM +
    retry/backoff + response caching), `memory.py`, `listing.py`, `vision.py`, `marketing_agent.py`,
    `integrations/base.py` (connector adapter seam, not wired yet)
  - `routes/` → one module per domain (workspaces, items, listings, events, vision, agent, suggestions,
    assistant, brief, integrations, inbox); `server.py` is now just the app factory + startup/shutdown.
- **Fixed the `WORKSPACE_CREATED` event bug** — `create_workspace` previously logged `ITEM_CREATED`;
  it now logs `WORKSPACE_CREATED` via the typed `EventType` enum (verified in tests and live HTTP).
- **Added DB indexes** (HANDOVER §24 set) via `db/indexes.py`, applied on startup — no collection scans
  as data grows (items, listings, events, suggestions, performance, price_history, integrations, inbox,
  workspaces).
- **LLM resilience** in `services/llm.py`: retry with exponential backoff on transient errors
  (default 3 attempts, 1s/2s), in-memory response cache (TTL 600s, max 256 entries; vision never
  cached), immediate raise on JSON parse failures. Tunable via `LLM_MAX_RETRIES`,
  `LLM_RETRY_BASE_DELAY`, `LLM_CACHE_TTL`, `LLM_CACHE_MAX_ENTRIES`.
- **Test infrastructure**: legacy `backend/test_*.py` scripts relocated into `backend/tests/` with
  skip guards (they need a real LLM key / the preview deployment); new fully-local tests run against
  an in-memory Mongo (`mongomock://`) with a mocked LLM — `tests/test_api.py` (tenant isolation,
  Control Layer, event fix), `tests/test_helpers.py`, `tests/test_llm.py` (retry/backoff/cache).
- `backend/.venv/` is a local virtualenv; the LLM layer uses the public `openai` SDK (import is
  now guarded so the app boots without it; LLM calls fail loudly when it/key is missing).

**Why**
- The documented immediate next actions: clean up the monolith before the next feature wave, add
  indexes (HANDOVER §23–24), and add LLM retry/backoff + caching before auth lands.

**Impact**
- 40/40 local tests pass (plus 2 skipped LLM-POC tests that require a real key); uvicorn smoke test
  passes over HTTP; route table identical to pre-refactor.
- Backend is now modular and unit-testable; future changes have a local safety net without needing
  the private LLM package or the preview deployment.

**Follow-ups (not yet done)**
- Purge preview test data (needs preview DB access).
- Authentication (HANDOVER §25) — still the top production priority.
- Real TradeMe connector behind `services/integrations/base.py`.
- Object storage for base64 images; background queue for `analyze-all`.

### Session — Workspace Hardening & Full Engineering Handover
**What changed**
- Audited the entire codebase (backend routes, tenant scoping, frontend wiring, design system).
- Ran a manual cross-workspace isolation test (curl) — passed.
- Ran the comprehensive backend testing agent focused on multi-tenant isolation:
  **27/27 scenarios passed, ZERO cross-workspace leakage** (`test_reports/iteration_4.json`).
  Regression suites saved: `backend/test_workspace_isolation.py`, `..._extended.py`.
- Produced the full handover package: `docs/HANDOVER.md` (35 sections), `PROJECT_STATE.md`, and this
  living diary. Updated `plan.md` to reflect Phase 11 (workspace verification) status.

**Why**
- Owner directive: verify & harden the multi-business foundation before any new features; then
  document thoroughly for handover as context/credits are exhausted.

**Impact**
- The tenant-isolation foundation is now trustworthy and evidenced. The project is fully documented
  for a cold-start by another team/agent.

**Follow-ups (not yet done)**
- Cosmetic: `create_workspace` logs `ITEM_CREATED` → should be `WORKSPACE_CREATED`.
- Relocate `backend/test_*` into a `tests/` package; purge preview test data.
- Backend refactor into routers/services + add DB indexes (HANDOVER §23–24).
- LLM retry/backoff + caching. Then authentication (HANDOVER §25).

### Earlier sessions (reconstructed from plan.md, ProductionReview.md, code)
- **Phase 1–2:** LLM listing POC (`test_core.py`) → MVP app (items, listing generation, events).
- **Phase 3:** Item schema upgrade (image/cost/category); persisted listings; uppercase event types.
- **Phase 4:** Dark industrial design system + sidebar navigation + core pages.
- **Phase 5:** Marketing Intelligence Agent (performance + suggestions + brief + price history).
- **Phase 6:** Visual Intelligence (`/ai/vision/analyze`) + value estimation; workflow auto-fill.
- **Phase 7:** Control Layer + Action Queue + Live Assistant (text + Web Speech voice) + widgets +
  daily briefing + `client-events` telemetry.
- **Phase 8:** Command Center dashboard + Integration Hub (simulated) + Smart Inbox.
- **Phase 9:** Production review/consolidation (partial) — `ProductionReview.md`, standardized API
  layer + shared LLM helper + unified tokens.
- **Phase 10:** Multi-Business Workspaces — backend `workspace_id` scoping + `get_wid` + legacy
  migration; frontend context/switcher/settings + header interceptor.

---

## Key design decisions (rationale)
- **Stateless, header-based tenancy (`X-Workspace-Id`)** — cache-friendly and JWT-forward-compatible.
- **Silent fallback to default workspace** on missing/invalid header — UX-safe pre-auth; make strict
  post-auth.
- **UUID ids, `_id` always excluded, UTC datetimes** — portability + clean isolation.
- **One shared `call_llm` + strict-JSON prompts + `extract_json`** — consistency + resilient parsing.
- **Approval-gated Control Layer** — AI never acts autonomously; every mutation auditable via events.
- **Per-workspace AI memory injected into all prompts** — tailored, isolated AI behavior per business.
- **Simulated-but-labeled integrations/signals** — full UX now, real APIs later without UI churn.
- **Defer auth but ship auth-ready libs/design** — velocity now, no painful refactor later.

---

## Lessons learned
- Centralized write/read patterns made retrofitting multi-tenancy tractable; an automated isolation
  suite converted "we think it's isolated" into "we proved it (100%)."
- The Control Layer is a trust feature, not overhead — it's what makes an AI that edits listings safe.
- Honesty about simulated data preserves product credibility during the build-out.
- The monolith accelerated the MVP but now needs modularization before the next feature wave.
- Keeping plan/handover/diary current is essential given session/token limits.

---

## Critique & risks (current)
- **No auth** is the biggest gap for real use; `/workspaces/{id}` routes are open by id.
- **LLM latency/cost** dominates UX; no retry/backoff/caching yet.
- **base64 images** bloat documents/payloads; move to object storage.
- **No DB indexes** — will degrade as data grows.
- **Monolithic backend** — testability/scaling limits.

---

## Roadmap (6 months, condensed — see HANDOVER §32)
1. Refactor + indexes + LLM resilience.
2. Authentication & authorization; lock CORS/rate limits.
3. Real TradeMe connector (OAuth, approval-gated).
4. Financials + object storage for images.
5. Communications hub + workflow engine (Kanban/Calendar/Timeline).
6. Global search + scheduled analysis + notifications + roles/audit + workspace import.

---

### Session — Error sweep: images, tokens & boots
**What changed**
- **Removed image assets:** deleted the placeholder PWA icons (`frontend/public/icon-*.png`)
  and their references (`index.html`, `manifest.json`), plus the stray `consolistrix/`
  duplicate archive that carried concept PNGs. The shipped app now contains zero image files.
- **Stopped the LLM "context length exceeded" error:** a raw 5MB phone photo becomes ~6.7MB
  of base64, which providers count as ~1.6M tokens and reject. Images are now compressed
  client-side (`compressImage` in `lib/utils.js`, ~1024px JPEG) before vision analysis,
  storage, or item creation; the backend also rejects oversized payloads (vision route,
  `store_image`, `ItemCreate.image`). This also kills the base64 storage bloat.
- **Stopped token-invalidation on restart:** `JWT_SECRET` unset now generates a persistent
  dev secret at `backend/.jwt_secret` (gitignored) instead of an ephemeral one; tests use a
  >=32-byte secret so the InsecureKeyLength warning is gone too.
- **Resilient boot:** missing/placeholder `MONGO_URL`/`DB_NAME` fall back to in-memory
  mongomock (dev) with a loud warning; missing/placeholder `REACT_APP_BACKEND_URL` falls back
  to `http://localhost:8000` so a fresh checkout no longer floods the console with failed
  requests. Production env vars still take precedence.

**Impact**
- Backend suite: **88 passed / 3 skipped**, warnings down 33 → 18. Frontend production build
  clean. `uvicorn server:app` and the CRA app both boot with zero configuration.

**Follow-ups (not yet done)**
- Real object storage (S3) for images; the Mongo `image_blobs` store remains the default.
- Auth is still staged: set `JWT_SECRET` (or rely on `backend/.jwt_secret`) + `AUTH_REQUIRED=true`
  for the locked-down mode.

---

_Keep appending. This diary is the narrative memory of Listrix._

---

### Session — Zero-cost / open-source migration (no paid APIs, hosts, or domains)

**Why:** the owner asked to strip every pay-per-use API, paid host, and domain dependency and run
the whole stack on open-source software, using GitHub for CI/hosting.

**What changed**
- **LLM is now local-first and open source.** `LLM_BASE_URL` defaults to
  `http://localhost:11434/v1` (local Ollama) and `LLM_MODEL` to `llama3.2-vision` (open weights).
  The hard `LLM_API_KEY` gate was removed — local servers accept any dummy key, so AI features need
  no account and no billing. A blank/empty `LLM_BASE_URL` is treated as unset, so a missing env var
  can never silently fall back to `api.openai.com` (which would be a paid call).
- **Google Fonts CDN removed.** Inter + Roboto Mono are self-hosted as variable woff2 files in
  `frontend/src/fonts/` (webpack-bundled, works under GitHub Pages subpaths); `index.html` and
  `index.css` no longer hit `fonts.googleapis.com`/`fonts.gstatic.com`.
- **UI label corrected:** AI Control page now reads "provider: local ollama · model: llama3.2-vision
  (open-source)" instead of "openai · gpt-5.4".
- **Free hosting story:** `.github/workflows/ci.yml` (backend pytest + frontend build) and
  `.github/workflows/pages.yml` (GitHub Pages deploy) added; root `docker-compose.yml` + backend/
  frontend Dockerfiles self-host MongoDB Community + FastAPI + nginx on one machine; `README.md`
  and MIT `LICENSE` added; git repo initialized (`.gitignore` covers env/venv/build secrets).
- **Docs updated:** `BUILDER_BRIEF.md` rewritten around the free stack (Ollama, GitHub Pages,
  Docker Compose, no domain required); `HANDOVER.md` (§26–30 + AI/arch sections), `PROJECT_STATE.md`,
  and `ProductionReview.md` de-OpenAI'd. Live marketplace connectors (TradeMe/Facebook/Gmail)
  remain staged/optional — off by default, simulated without credentials, never required.
- **Tests:** live-LLM POCs (`test_core.py`, `test_core2.py`) now skip unless
  `LISTRIX_RUN_LIVE_LLM_TESTS=1`; the key-required unit test became a "no key needed" test.

**Impact**
- Backend suite: **88 passed / 3 skipped**. Frontend production build clean. No external runtime
  dependency that costs money: local LLM, local DB, static frontend on GitHub Pages, CI on GitHub
  Actions, backend on any machine you control.

**Follow-ups (not yet done)**
- Live connector validation with real credentials (optional external marketplaces).
- Sales P&L refinements: per-sale COGS + marketplace payout reconciliation.
- Object storage for images (S3-compatible/MinIO — both open source) if Mongo blobs outgrow.
