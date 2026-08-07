# Listrix — Updated plan.md (Consolidated)

## 1) Objectives
- Deliver a **stable, preview-loadable** full-stack app (React + FastAPI + MongoDB) that functions as a **dark industrial resale operations control room**.
- Preserve and harden the foundation for a commercial SaaS:
  - **Multi-Business Workspaces** with **complete data isolation** (no cross-tenant leakage)
  - **Control Layer**: AI never executes changes or external actions without explicit user approval
  - **Production-quality code** (no placeholder screens; simulated integrations allowed only as architecture)
- Maintain core, working flows:
  - **Item creation** (name/description/condition/image/cost)
  - **AI listing generation** (marketplace title/description/suggested price/hashtags)
  - **Event logging** for every meaningful action
- Add layered intelligence (non-decorative, tied to real items/listings/events):
  - **Marketing Intelligence Agent** (performance + suggestions + daily brief)
  - **Visual Intelligence** (image-based identification + category/brand/features + value range)
  - **Market Awareness (architecture)** for competitor comparisons (no scraping yet)
- Provide operational surfaces:
  - **Voice Interface** (spoken-style responses + structured recommendations)
  - **Widget System** (auto-rotating dashboard widgets)
  - **Command Center** dashboards and an **Action Queue**
- Documentation and maintainability:
  - Maintain a living `docs/Listrix_Development_Diary.md` documenting decisions, architecture, critique, and roadmap
  - Reduce duplication and technical debt; improve performance where practical

## 2) Implementation Steps

### Phase 1 — Core POC (Isolation) — LLM Listing Generation ✅ COMPLETED
**User stories (POC)**
1. As a user, I can run a script and see the AI return a listing title/description from my item input.
2. As a user, I can see the AI output parsed into the required JSON fields.
3. As a user, I can confirm the AI output is consistent enough to power a UI.
4. As a user, I can quickly re-run the script with different inputs to validate stability.
5. As a developer, I can see clear errors if the key/model/response format fails.

**Steps (done)**
1. Created `backend/test_core.py` using `services.llm.call_llm` (OpenAI-compatible SDK, `LLM_API_KEY`).
2. Enforced strict JSON output, parsed and validated it.
3. Verified success across 3 consecutive runs.

---

### Phase 2 — MVP App Development (Backend + Frontend) ✅ COMPLETED
**User stories (V1)**
1. As a user, I can open the app and navigate pages.
2. As a user, I can create an item.
3. As a user, I can generate a listing and see results in the UI.
4. As a user, I can refresh and still see saved data.
5. As a user, I can view logged events.

**Steps (done)**
- Implemented backend endpoints and MongoDB collections.
- Implemented frontend pages wired to backend.
- Verified end-to-end in preview.

---

### Phase 3 — Item System Upgrade ✅ COMPLETED
**Upgrades implemented**
- Item schema updated to: `name, description, condition, image (optional), cost (optional)`.
- Listings persisted; added `GET /api/items` and `GET /api/listings`.
- Events updated to uppercase types: `ITEM_CREATED`, `LISTING_GENERATED`.
- Dashboard upgraded to show **recent items**, **AI listings**, and **activity feed**.

---

### Phase 4 — Dark Industrial Design System + Navigation ✅ COMPLETED
**Upgrades implemented**
- Global dark industrial theme tokens (charcoal background + orange accent).
- Left sidebar navigation and core pages.
- Item cards, event timeline UI, workflow stepper.

---

### Phase 5 — Marketing Intelligence Agent (Backend) ✅ COMPLETED
**Goal**: a real marketing manager layer that produces insights tied to real inventory, listing data and history.

**Backend features implemented**
- Analysis endpoints:
  - `POST /api/ai/analyze/{item_id}` → performance + suggestions
  - `POST /api/ai/analyze-all` → batch analysis
- Storage:
  - `performance` collection
  - `suggestions` collection
  - `price_history` collection
- One-click (approved) actions:
  - `POST /api/suggestions/{id}/apply`
  - `POST /api/suggestions/{id}/dismiss`
- Daily brief:
  - `POST /api/brief/generate`, `GET /api/brief/latest`
- Market/competitor placeholder:
  - `GET /api/competitors/{item_id}` (structure only)

**POC verification (done)**
- Marketing agent structured output tested and validated.

---

### Phase 6 — Visual Intelligence + Value Estimation (Backend + Integration) ✅ COMPLETED
**Goal**: “visual resale expert + pricing analyst + marketing strategist” image understanding integrated into item creation and marketing.

**Status update**
- `POST /api/ai/vision/analyze` is implemented.
- Vision outputs can be persisted to items when `item_id` is provided.
- Events are emitted (`IMAGE_ANALYSED`, `VALUE_ESTIMATED`).

---

### Phase 7 — Control Layer + Voice + Widgets + Live Assistant + Daily Briefing (Backend + Frontend) ✅ COMPLETED
**Status update**
- Control-layer approval logging exists (`USER_APPROVED_ACTION`) and suggestion apply/dismiss flows are approval-based.
- Assistant endpoint exists (`POST /api/ai/assistant`) with voice event logging.
- Widget telemetry endpoint exists (`POST /api/client-events` with whitelist).
- Daily brief endpoints exist (`POST /api/brief/generate`, `GET /api/brief/latest`).

---

### Phase 8 — Command Center + Integration Hub + Smart Inbox ✅ COMPLETED (Architecture / Simulation)
**Status update**
- Integration Hub connectors remain simulated but structurally modular (per-workspace seeded connectors; connect/sync endpoints).
- Inbox is simulated but structurally scoped per workspace.

---

### Phase 9 — Production Review / Consolidation ⚠️ PARTIALLY COMPLETED
**Goal**: reduce tech debt and duplication; standardize patterns; improve maintainability.

**Status**
- `docs/ProductionReview.md` exists.
- Consolidation/refactor remains pending after workspace hardening.

---

### Phase 10 — Multi-Business Workspaces (Backend + Frontend Wiring) ✅ IMPLEMENTED (Verification Pending)
**Goal**: complete tenant isolation across businesses.

**What’s implemented**
- Backend:
  - `workspace_id` added and enforced across scoped collections.
  - `get_wid` dependency reads `X-Workspace-Id` and scopes most routes.
  - Auto-migration: unscoped docs are stamped into default workspace.
- Frontend:
  - Axios interceptor injects `X-Workspace-Id` from `localStorage`.
  - `WorkspaceContext` + `WorkspaceSwitcher` + `Settings` workspace configuration page.

**Progress in this session**
- Full backend `server.py` review completed: nearly all reads/writes are scoped by `workspace_id`.
- Manual curl isolation test **passed**:
  - Workspace A sees only its own items/events
  - Workspace B sees only its own items/events
  - Invalid workspace header falls back to default (UX-safe; must document)
- Frontend wiring verified:
  - `QueryClientProvider` wraps the app
  - `WorkspaceProvider` is active
  - workspace switching invalidates queries and the API layer injects headers

**Known minor concerns (to address after verification)**
1. `GET/PUT/EXPORT /workspaces/{ws_id}` are not scoped to “current workspace” (acceptable without auth; must be secured once auth exists).
2. `get_wid` silently falls back to default on invalid IDs (safe for UX; document and consider strict mode later).
3. `create_workspace` logs `ITEM_CREATED` (semantic cleanup: should be `WORKSPACE_CREATED`).

---

### Phase 11 — Workspace Verification & Hardening (P0) ✅ COMPLETED
**Goal**: prove (and enforce) true multi-tenant isolation and prevent security/data leaks.

**Backend verification steps**
1. **Route-by-route audit**
   - Confirm every endpoint that touches scoped collections includes `wid: str = Depends(get_wid)`.
   - Confirm every query filter contains `workspace_id: wid`.
   - Confirm every insert includes `workspace_id: wid`.
2. **Cross-workspace leakage test suite (automated)**
   - Create 2+ workspaces.
   - Ingest items/listings/events/suggestions/performance/briefs/integrations/inbox in each.
   - Verify reads never return other workspace data.
   - Verify mutation endpoints (`apply`, `dismiss`, `edit`, `vision persist`, `inbox refresh`, `integrations connect/sync`) cannot affect another workspace.
3. **Header/edge-case testing**
   - Missing header behaviour is consistent.
   - Invalid workspace header behaviour is documented; consider feature flag for strict mode later.
4. **DB migration validation**
   - Ensure pre-existing docs have `workspace_id` stamped.
   - Add MongoDB indexes for `workspace_id` + common query keys where beneficial.

**Frontend verification steps**
1. Workspace switching regression test
   - Switch workspaces and verify all data panels update (items/listings/events/inbox/intelligence).
2. Header injection validation
   - Confirm `X-Workspace-Id` is present for all API calls.
3. UI integrity checks
   - No layout collisions (AI assistant floating button vs workspace switcher vs badges) across breakpoints.

**Fix & optimize steps (only after tests prove issues exist)**
- Tighten any missing scoping in queries/inserts.
- Standardize API response patterns if needed.
- Minor semantic cleanup (event names).

**Exit criteria (must pass)**
- No cross-tenant reads.
- No cross-tenant writes.
- Workspace switching yields correct isolated datasets.
- Evidence captured in `test_reports/`.

---

### Phase 12 — Backend Refactor / Indexes / LLM Resilience (P1) ✅ COMPLETED (Backend)
**Goal**: make the codebase maintainable and scalable without changing product behaviour.

**Done (backend)**
1. Backend refactor (route parity 33/33 verified, zero behavior change)
   - `server.py` → app factory only; `routes/` split by domain (workspaces, items, listings, events,
     vision, agent, suggestions, assistant, brief, integrations, inbox)
   - `services/` → `llm.py` (shared LLM + retry/backoff + cache), `memory.py`, `listing.py`,
     `vision.py`, `marketing_agent.py`, `events.py` (typed `EventType` enum), `integrations/base.py`
   - `db/` → `indexes.py` (ensure_indexes on startup), `migrations.py`
   - `models/` → Pydantic models grouped by domain; `config.py` + `deps.py` + `utils.py`
2. Unified patterns
   - Centralized event logging via `services/events.log_event`; typed `EventType` enum.
   - Fixed `WORKSPACE_CREATED` event (was wrongly logging `ITEM_CREATED`).
3. Performance improvements
   - Added the full recommended index set (HANDOVER §24) via `db/indexes.py` on startup.
   - LLM retry (exponential backoff) + response caching in `services/llm.py` (vision never cached).
4. Testability
   - Legacy `backend/test_*.py` moved to `backend/tests/` with skip guards.
   - New fully-local tests (mongomock in-memory Mongo + mocked LLM): 40 passing.

**Still open**
- Frontend accessibility + UX polish (focus states, keyboard nav, responsive layout).
- Object storage for base64 images; background queue for `analyze-all`.

---


### Phase 13 — Authentication & Authorization (P0) ✅ COMPLETED (Backend-first, staged)
**Goal**: secure every `/api` route with email/password + JWT; attach workspaces to users; lock
down workspace ownership; rate-limit LLM endpoints (HANDOVER §25).

**Done**
1. `users` collection + `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`
   (`routes/auth.py`, `services/auth.py` — bcrypt hashing, HS256 JWT, `JWT_SECRET`/`JWT_TTL_SECONDS`).
2. `owner_id` on workspaces; register creates an owned default workspace (+ seeded connectors).
3. Ownership guards on `/workspaces/{id}` GET/PUT/export (403 for other users' workspaces).
4. Auth-aware tenancy: `get_wid` validates `X-Workspace-Id` belongs to the authenticated user
   (403 otherwise) and falls back to the user's default workspace when no header is sent.
5. LLM endpoint rate limiting (`services/ratelimit.py`, sliding window, default 30/min/workspace).
6. Staged enforcement: `AUTH_REQUIRED=false` (default) preserves the pre-auth preview behavior;
   `AUTH_REQUIRED=true` returns 401 on every `/api` route without a valid token.
7. Frontend: axios Bearer-token interceptor, `AuthContext` (login/register/logout/hydrate),
   `/login` page, header Sign in/out control — app keeps working without auth in grace mode.

**Verification**: 12 new auth tests (52/52 total local tests passing); live uvicorn smoke tests in
both grace and strict modes (`test_reports/iteration_6.json`).

**Still open**
- Per-workspace usage quotas/budgets; CORS origin lockdown for multi-origin exposure; token refresh.


### Phase 14 — Real TradeMe Connector (P1) ✅ COMPLETED (Staged)
**Goal**: wire the first real marketplace behind the existing connect/sync endpoints —
OAuth 1.0a, encrypted tokens at rest, and approval-gated sync. Never auto-post.

**Done**
1. `services/integrations/trademe.py` — real TradeMe adapter: 3-legged OAuth 1.0a
   (request token → authorize URL → verifier callback), live sync of the seller's listings +
   market anchors, pending `reduce_price` suggestions with `params.new_price` (control layer).
2. Encrypted token storage: Fernet (`CONNECTOR_ENCRYPTION_KEY`, dev fallback from `JWT_SECRET`);
   `GET /integrations` never exposes `tokens`/`config`.
3. New route `POST /api/integrations/{platform}/oauth/callback`; adapter registry
   (`services/integrations/__init__.py`) with staged dispatch — when `TRADEME_CONSUMER_KEY/SECRET`
   are unset, the legacy simulated toggle/sync is preserved (preview + isolation suite intact).
4. Frontend: IntegrationHub opens the authorize URL, handles the OAuth callback redirect
   (submits the verifier), and updates the connector copy.

**Verification**: 6 new tests (OAuth flow, encryption at rest, cross-check isolation, sync →
pending suggestions, no listing mutation, idempotent re-sync, search fallback, threshold skip;
legacy preservation). Full local suite 58 passed / 2 skipped (`test_reports/iteration_7.json`).

**Still open**
- Live end-to-end validation against TradeMe with real credentials + callback URL.
- Other real connectors (Facebook Marketplace, Gmail) behind the same adapter seam.

### Phase 15 — Financials (P1) ✅ COMPLETED
**Goal**: money math on real data — fees, tax, net profit and margin per item, per category and
in total, derived from cost, listing price (or value estimate) and workspace settings.

**Done**
1. `config.py` — `MARKETPLACE_FEE_RATE = 0.079` (7.9% marketplace fee).
2. `services/financials.py` — `compute_financials(wid)`: workspace currency/tax_rate, per-item rows
   (cost, price from listing → fallback `value_estimate.mid`, gross, fees, tax, net, margin_pct),
   totals (invested, potential_revenue, net_profit, net_margin_pct), `by_category` aggregation,
   and a `note` stating figures are potential. Items without cost AND price are skipped.
3. `routes/financials.py` — `GET /api/financials` (workspace-scoped via `get_wid`).
4. `tests/test_financials.py` — 4 new local tests: exact math (cost 100 / price 200 → fees 15.80,
   tax 10.00, net 74.20, margin 37.1%), value-estimate fallback for unlisted items, workspace
   isolation, currency passthrough + default 0% tax, and skip-items-without-numbers.
5. Frontend: `getFinancials` in `lib/api.js`, `useFinancials` in `lib/queries.js`, new `Financials`
   page (totals cards, category table, top-items table, currency-aware money formatting), registered
   in Sidebar NAV + AppShell titles/mobile nav + App route.

**Verification**: 4 new tests; full local suite 62 passed / 2 skipped
(`test_reports/iteration_8.json`); esbuild syntax-check passed for all touched FE files.

**Still open**
- Object storage for base64 images + background queue for `analyze-all`.

### Phase 15b — Sales Tracking → Realized P&L (P1) ✅ COMPLETED
**Goal**: record completed sales so Financials shows REALIZED profit next to potential figures.

**Done**
1. `models/item.py` — `sold`, `sold_at`, `sale_price` fields.
2. `routes/items.py` — `POST /api/items/{id}/mark-sold` (sale_price, optional sold_at; 422 on
   negative price, 404 cross-workspace) and `POST /api/items/{id}/mark-unsold` (revert).
3. `services/events.py` — `ITEM_SOLD` / `ITEM_UNSOLD` event types (audit trail).
4. `services/financials.py` — sold items use `sale_price` → realized totals
   (`realized_revenue`, `realized_net_profit`, `realized_margin_pct`); unsold stay potential
   (`potential_*`); combined `net_profit`/`net_margin_pct`; per-row `status` + `sale_price`;
   per-category `sold` counts. Response `note` explains realized vs potential.
5. Frontend — ItemDetail "Mark Sold" flow (inline sale-price input, confirm, revert), ItemCard
   "Sold · price" chip, Financials page realized/potential stat cards + Status column.

**Verification**: 4 new tests (mark-sold endpoint + event, validation/isolation, revert, realized
vs potential math — sold 220/cost 100 → realized net 90.62; unsold 200/cost 100 → potential net
74.20). Full local suite 66 passed / 2 skipped (`test_reports/iteration_9.json`); esbuild
syntax-check passed for all touched FE files.

**Still open**
- Object storage for base64 images + background queue for `analyze-all`.

### Phase 16 — Object Storage for Images (P1) ✅ COMPLETED
**Goal**: stop embedding base64 images in item documents; store blobs out-of-line with
server-side thumbnails (S3-swappable interface).

**Done**
1. `services/storage.py` — Mongo-backed blob store (`image_blobs`) + Pillow thumbnails
   (320px, JPEG q75); `data_uri` helpers. Items keep a tiny `image_id` reference.
2. `POST /api/items/{id}/image` (data URI or base64 → stores blob + thumbnail, sets
   `image_id`, logs `IMAGE_UPLOADED`) and `GET /api/images/{id}?thumb=1` (serves raw bytes,
   workspace-scoped 404). Legacy inline `image` still supported for old data.
3. Frontend `imageSrc(item, thumb)` helper; ItemCard/ItemDetail/Kanban render thumbnails
   through `/api/images/{id}`; Workflows uploads via the new endpoint after item creation.

**Verification**: blob/thumbnail round-trip, smaller thumb, no base64 in item docs,
cross-workspace 404, invalid data → 400.

### Phase 17 — Background Jobs, Notifications & Scheduler (P2) ✅ COMPLETED
**Goal**: make heavy operations async and surfaced, with in-app notifications.

**Done**
1. `services/jobs.py` + `GET /api/jobs/{id}` — persisted job queue; `analyze-all` now enqueues
   a job (`POST /api/ai/analyze-all` returns `{job_id, status, total}`) and a bounded worker
   (concurrency 3) updates progress. Frontend `runAnalysisJob()` polls to completion.
2. `services/notifications.py` + `GET /api/notifications`, `POST /notifications/read`,
   `POST /notifications/{id}/read` — fired on sale recorded, stage moves, etc.
3. `services/scheduler.py` — opt-in periodic tick (`SCHEDULER_ENABLED=true`,
   `SCHEDULER_INTERVAL_MINUTES`, default off so tests are deterministic).

### Phase 18 — Real Facebook & Gmail Connectors + Comms Hub (P1) ✅ COMPLETED (Staged)
**Goal**: second and third real connectors behind the adapter seam; buyer messages land in
the inbox and replies stay approval-gated drafts.

**Done**
1. `services/integrations/facebook.py` — Graph API page-token adapter (`FACEBOOK_PAGE_TOKEN`):
   connect stores the token encrypted (Fernet), sync maps lower Marketplace anchors to pending
   `reduce_price` suggestions; never posts. Unconfigured → legacy simulated toggle preserved.
2. `services/integrations/gmail.py` — Gmail API token adapter (`GMAIL_ACCESS_TOKEN`): connect
   stores token; sync pulls recent messages into the inbox as real `BUYER_MESSAGE`s (linked to
   items by name match); replies are drafts only (`POST /api/inbox/{id}/reply`), never auto-sent.
3. `routes/inbox.py` — refresh merges real Gmail messages when connected; `mark-read` + reply
   draft endpoints (`INBOX_REPLY_DRAFTED` event). Frontend Inbox: reply box, draft display,
   read toggle, Gmail source tag.

### Phase 19 — Workflow Engine: Stages + Kanban + Timeline (P2) ✅ COMPLETED
**Goal**: lifecycle states for items and a board/timeline view.

**Done**
1. Item `stage` (`inventory|listed|sold|archived`) with validated transitions
   (`POST /api/items/{id}/stage`, `ITEM_STAGE_CHANGED` event); `mark-sold`/`mark-unsold` keep
   stage consistent.
2. Frontend Workflows page gains tabs: **Kanban** (4 columns, per-card stage select, thumbnails)
   and **Timeline** (events + sales grouped by day).

### Phase 20 — Global Search, CSV Import & Event Analytics (P2) ✅ COMPLETED
**Goal**: find anything in a workspace fast, bulk-load inventory, and see activity trends.

**Done**
1. `GET /api/search?q=` — items/listings/events/inbox, regex-scoped, min 2 chars; frontend
   Search page + header search box.
2. `POST /api/workspaces/import` — CSV bulk item creation (`ITEMS_IMPORTED` event, per-row
   errors); Settings → Data & Backup tab UI.
3. `GET /api/analytics?days=` — event totals, top types, per-day series, inventory/sold/listings/
   pending counts; Command Center analytics panel.

### Phase 21 — Multi-User Roles & Members (P1) ✅ COMPLETED (Staged)
**Goal**: owners can invite collaborators; roles are enforced on workspace management.

**Done**
1. `workspace_members` collection + `GET/POST /workspaces/{id}/members`,
   `DELETE /workspaces/{id}/members/{member_id}` — owner-only invite/remove; members can view;
   non-members 403; owner immovable.
2. Settings → Team Members tab (invite/role/remove UI). Full route lockdown stays behind
   `AUTH_REQUIRED=true` per the staged auth design.

## 3) Next Actions
1. ✅ **Phase 11 (P0): Workspace isolation verified 100%** — 27/27 scenarios, zero leakage
   (`test_reports/iteration_4.json`); legacy suites relocated to `backend/tests/`.
2. ✅ **Phase 12 (backend): modular refactor + indexes + LLM retry/backoff/caching** — route parity
   33/33, 40 local tests passing (`test_reports/iteration_5.json`).
3. ✅ **Authentication (Phase 13)** — email/password + JWT, ownership guards, auth-aware tenancy,
   LLM rate limiting, staged `AUTH_REQUIRED` enforcement. Deploy with `JWT_SECRET` set; then add
   usage quotas + CORS lockdown.
4. ✅ **Real TradeMe connector (Phase 14)** — OAuth 1.0a, encrypted tokens, approval-gated sync;
   staged behind `TRADEME_CONSUMER_KEY/SECRET`. Next: live validation + other connectors.
5. ✅ **Financials (Phase 15)** — fees/tax/net-profit/margin reporting (`GET /api/financials`) +
   frontend Financials page; 62 passed / 2 skipped (`test_reports/iteration_8.json`).
6. ✅ **Sales tracking (Phase 15b)** — `mark-sold`/`mark-unsold` endpoints, ITEM_SOLD events,
   realized vs potential P&L in `/api/financials`, Mark Sold UI; 66 passed / 2 skipped
   (`test_reports/iteration_9.json`).
7. ✅ **Object storage + background queue (Phase 16–17)** — `image_blobs` + thumbnails,
   persisted jobs for `analyze-all`, in-app notifications, opt-in scheduler.
8. ✅ **Real connectors + comms hub (Phase 18)** — Facebook (Graph API) + Gmail (API) adapters,
   staged behind env tokens; inbox reply drafts.
9. ✅ **Workflow engine (Phase 19)** — item stages + Kanban + Timeline.
10. ✅ **Search / import / analytics (Phase 20)** — `GET /api/search`, CSV import, event analytics.
11. ✅ **Multi-user roles (Phase 21)** — workspace members, owner-gated invite/remove.
12. ✅ **Emergent removal + builder packaging (Phase 22)** — AI moved to the public `openai` SDK
    against any OpenAI-compatible endpoint (`LLM_API_KEY`/`LLM_BASE_URL`/`LLM_MODEL`; free options:
    Groq, OpenRouter, local Ollama). Emergent scrubbed from code, tests, configs and docs. PWA
    shell (`manifest.json`, `sw.js`, icons) + `capacitor.config.json` for Android APK wrapping;
    `docs/BUILDER_BRIEF.md` written as the owner→builder handoff. Backend suite 83 passed / 3
    skipped; 84 frontend files esbuild-clean; package rebuilt as `Listrix_Consolidated_Project_UPDATED.zip`.
13. ✅ **Connection Wizard (Phase 23)** — in-app setup for live TradeMe/Facebook/Gmail: paste
    credentials (encrypted per workspace), one-click live connection test, guided step-by-step UI,
    disconnect/reset. New endpoints: `integrations/{platform}/config|test|disconnect` +
    `GET /integrations/status`. Env-var staging still supported as fallback. Backend suite
    **88 passed / 3 skipped**; production `yarn build` succeeds.
14. ✅ **Command Center polish (Phase 24)** — dashboard upgraded to the owner's reference layout:
    Activity Overview area chart (real analytics, event-stream fallback) + Inventory Snapshot data
    table (AI confidence, est. value, click-through rows). New `DashboardChart.js` /
    `DashboardTable.js`; production `yarn build` succeeds.
15. ✅ **Open-source / zero-cost migration (Phase 25)** — LLM defaults to LOCAL Ollama
    (`LLM_BASE_URL=http://localhost:11434/v1`, `LLM_MODEL=llama3.2-vision`; API-key gate removed;
    blank base URL can no longer fall back to a paid endpoint), Google Fonts CDN removed
    (self-hosted Inter/Roboto Mono), `AIControl.js` label corrected, GitHub Actions CI +
    GitHub Pages deploy + root `docker-compose.yml` + Dockerfiles added, README/MIT LICENSE added,
    git repo initialized. Docs (BUILDER_BRIEF/HANDOVER/PROJECT_STATE/diary) updated to the free,
    open-source stack. Backend suite **88 passed / 3 skipped** (live-LLM POCs opt-in via
    `LISTRIX_RUN_LIVE_LLM_TESTS=1`); frontend production build clean.
16. ✅ **Owner feedback round (Phase 26)** — Stocksix inventory connector (wizard + encrypted
    creds + idempotent item sync via `GET /api/public/v1/inventory`), Integration Hub offline
    fallback so the wizard is never "missing", `GET /api/ai/status` probe + AI-status banner +
    real sidebar AI light, and the DJ-deck redesign (3D panels, glowing buttons, neon accents,
    animated equalizer bars). Backend **92 passed / 3 skipped**; frontend production build clean.
17. **Live end-to-end validation of TradeMe/Facebook/Gmail/Stocksix with real credentials; sales
    P&L refinements (cost-of-goods per sale, marketplace payout reconciliation).**

> Explicitly deferred: Authentication (design must not block future auth; lock down workspace routes once auth exists).
> Integrations remain simulated but must be modular and production-ready.

## 4) Success Criteria
- **Stability**: App loads in preview; all core pages/routes render under the dark industrial design.
- **Workspace isolation (P0)**:
  - All scoped collections strictly filtered by `workspace_id` on reads/writes.
  - No cross-workspace data leakage observed in automated and manual tests.
  - Workspace switching correctly reloads isolated datasets in the UI.
- **Core flows still work**:
  - `POST /api/items` creates items with workspace scoping.
  - `POST /api/ai/generate` creates listings with workspace scoping.
  - `GET /api/events` shows only workspace events.
- **Control Layer enforced**:
  - No AI-driven modifications happen without explicit user approval.
  - Approval events (`USER_APPROVED_ACTION`, `AI_SUGGESTION_APPLIED`) are logged.
- **Integrations architecture is modular**:
  - Connect/sync endpoints are scoped and simulate safely.
  - Designed so TradeMe can be the first real connector later with minimal code changes.
- **Documentation**:
  - `docs/Listrix_Development_Diary.md` exists and is updated as work progresses.
