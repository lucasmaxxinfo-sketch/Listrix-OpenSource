# PROJECT_STATE.md — Listrix (Fast Continuation Guide)

> Purpose: everything a new engineer or AI agent needs to resume Listrix development immediately,
> without prior context. For the full deep-dive, read `/app/docs/HANDOVER.md`.
> Last updated: Command Center polish session (dashboard Activity Overview chart + Inventory Snapshot table matching the owner's reference layout, wired into the live preview).

---

## 1. What Listrix Is (30 seconds)
A multi-tenant, AI **Business Operating System for resellers**. It turns inventory into AI-generated,
priced marketplace listings and runs an approval-gated **AI Marketing Manager** that scores listings
and suggests changes. Multiple isolated **workspaces** (businesses) per operator. Dark-industrial UI.

**Stack:** FastAPI + React 19 (CRACO) + MongoDB (self-hosted Community or in-memory for demo). **LLM = local
Ollama by default** (`LLM_BASE_URL=http://localhost:11434/v1`, `LLM_MODEL=llama3.2-vision`) via the `openai`
SDK — open weights, no API key, no paid service; the whole app is free/open-source to run
(`docker compose up`, GitHub Actions CI, GitHub Pages frontend). No auth required out of the box
(single operator; `AUTH_REQUIRED=true` locks it down).

---

## 2. Run / Verify Right Now
```bash
sudo supervisorctl status                     # backend, frontend, mongodb should be RUNNING
tail -n 80 /var/log/supervisor/backend.*.log   # backend health
cd /app/frontend && npx esbuild src/ --loader:.js=jsx --loader:.woff2=file --bundle --outfile=/dev/null   # FE compiles?
curl ${REACT_APP_BACKEND_URL}/api/             # {"message":"Listrix API is running"}
ollama serve && ollama pull llama3.2-vision   # local open-source AI (optional; AI features need it)
```
Preview URL: (deploy your own — see docs/BUILDER_BRIEF.md)

---

## 3. Golden Rules (do not violate)
- **Every scoped route** takes `wid: str = Depends(get_wid)` and filters/inserts `workspace_id`.
- **All backend routes live under `/api`.** Frontend calls `${REACT_APP_BACKEND_URL}/api` and the
  axios interceptor injects `X-Workspace-Id` from `localStorage.listrix_workspace_id`.
- **UUID string ids only; never ObjectId; always project out `_id`.** UTC timezone-aware datetimes.
- **AI never mutates without approval** — route changes through `suggestions` + the Control Layer.
- **Use shared helpers:** `call_llm`, `extract_json`, `log_event`, `build_ai_memory`.
- **Env/tooling:** `yarn` only (never npm); update `requirements.txt` via `pip install && pip freeze`;
  update `package.json` via `yarn add`; NEVER rewrite `.env`; never hard-code URLs/keys.
- **Never change** `REACT_APP_BACKEND_URL` or `MONGO_URL`.

---

## 4. Where Things Are
- **Backend (modular):** `/app/backend/server.py` (app factory only) + `routes/` (per domain) +
  `services/` (llm/memory/listing/vision/marketing_agent/events) + `db/` (migrations/indexes) +
  `models/` + `config.py`/`deps.py`/`utils.py`.
- **Frontend API layer:** `/app/frontend/src/lib/api.js` (axios + interceptor + endpoint fns).
- **Query hooks:** `/app/frontend/src/lib/queries.js` (TanStack Query + global invalidation).
- **Tenant state:** `/app/frontend/src/context/WorkspaceContext.js` (switch + branding injection).
- **Design tokens:** `/app/frontend/src/index.css` + `/app/frontend/tailwind.config.js`.
- **Pages:** `/app/frontend/src/pages/*` ; **Components:** `/app/frontend/src/components/*`.
- **Docs:** `/app/docs/HANDOVER.md` (full), `/app/docs/Listrix_Development_Diary.md` (log/roadmap),
  `/app/docs/ProductionReview.md`, `/app/docs/BUILDER_BRIEF.md` (plain-language handoff for a
  builder: run/host instructions, free AI options, PWA vs APK path, live-connection setup). **Plan:** `/app/plan.md`.
- **Tests:** `/app/backend/tests/` (legacy isolation/POC suites + new fully-local tests run on an
  in-memory Mongo with a mocked LLM); reports in `/app/test_reports/iteration_*.json`
  (iteration_4 = isolation 100%; iteration_5 = refactor regression 40/40).

---

## 5. Data Model (MongoDB) — all scoped by `workspace_id` except `workspaces`
`workspaces` (tenant; has branding + `ai_preferences` + `is_default`), `items`, `listings`
(join by `item_id` or `source_name`), `events` (audit log), `performance` (1/item), `suggestions`
(Action Queue: pending|applied|dismissed), `price_history`, `briefs`, `feedback` (learning loop),
`integrations` (5 seeded connectors/ws), `inbox`, `image_blobs` (object-storage images +
thumbnails), `jobs` (background analyze-all), `notifications` (bell feed), `workspace_members`
(roles: owner/member/viewer). See HANDOVER §4 for full field lists.
**No indexes yet** — see HANDOVER §24 for the recommended set.

---

## 6. Key Endpoints (all under /api, header-scoped)
Items: `POST/GET /items`, `GET /items/{id}` · Listing: `POST /ai/generate`, `GET /listings` ·
Vision: `POST /ai/vision/analyze` · Agent: `POST /ai/analyze/{id}`, `POST /ai/analyze-all`,
`GET /performance`, `GET /performance-intelligence`, `GET /market/signals` ·
Control Layer: `GET /suggestions`, `POST /suggestions/{id}/apply|dismiss|edit` ·
Assistant: `POST /ai/assistant` · Brief: `POST /brief/generate`, `GET /brief/latest` ·
Financials: `GET /financials` · Sales: `POST /items/{id}/mark-sold`, `POST /items/{id}/mark-unsold` ·
Images: `POST /items/{id}/image`, `GET /images/{id}?thumb=1` · Jobs: `POST /ai/analyze-all`, `GET /jobs/{id}` ·
Notifications: `GET /notifications`, `POST /notifications/read` · Stages: `POST /items/{id}/stage` ·
Search: `GET /search?q=` · Analytics: `GET /analytics` · Import: `POST /workspaces/import` ·
Members: `GET/POST /workspaces/{id}/members`, `DELETE /workspaces/{id}/members/{id}` ·
Inbox: `POST /inbox/refresh`, `POST /inbox/{id}/reply|read` ·
Workspaces: `GET/POST /workspaces`, `GET/PUT /workspaces/{id}`, `GET /workspaces/{id}/export` ·
Integrations: `GET /integrations`, `POST /integrations/{platform}/connect|sync` ·
Inbox: `POST /inbox/refresh`, `GET /inbox` · Events: `GET /events`, `POST /client-events` (whitelist).

---

## 7. Current Status
- **Multi-workspace isolation: VERIFIED 100% (27/27, zero leakage)** — `test_reports/iteration_4.json`.
- **Backend refactor COMPLETE (no behavior change; route parity 33/33)** — modular routes/services,
  typed `EventType` enum, `WORKSPACE_CREATED` event bug fixed, DB indexes applied on startup,
  LLM retry/backoff + response caching added (`test_reports/iteration_5.json`).
- **Auth implemented (staged)** — email/password + JWT, workspace ownership guards, auth-aware
  tenancy, LLM rate limiting; `AUTH_REQUIRED=true` locks all `/api` routes (52/52 local tests,
  `test_reports/iteration_6.json`).
- Core AI flows work against a real LLM — local Ollama (open weights) by default (listing/vision/agent/assistant/brief).
- **Auth:** implemented backend-first with staged enforcement (`AUTH_REQUIRED`, default false so
  the no-auth preview keeps working); flip to true once the login UI + JWT_SECRET are deployed.
- **Integrations:** TradeMe now supports the real OAuth + approval-gated sync flow when
  credentials are configured; other connectors + market signals remain SIMULATED by design.
- **Financials: COMPLETE** — `GET /api/financials` computes per-item + per-category + total fees,
  tax, net profit and margin from cost, price and workspace settings (currency, tax_rate);
  sold items use their actual `sale_price` (realized) while unsold items remain potential
  (`test_reports/iteration_9.json`).
- **Sales tracking: COMPLETE** — `POST /api/items/{id}/mark-sold|mark-unsold` records/reverts a
  sale (sale_price, sold_at), logs `ITEM_SOLD`/`ITEM_UNSOLD` events, and feeds realized P&L into
  Financials. UI: Mark Sold flow on Item Detail + Sold chips on item cards.
- **Platform layer (Phases 16–21): COMPLETE** — object storage + thumbnails (`image_blobs`,
  `POST /items/{id}/image`, `GET /images/{id}`), background jobs (`analyze-all` → persisted job
  queue + `GET /jobs/{id}`), in-app notifications + bell, opt-in scheduler, Facebook/Gmail
  adapters (staged, optional), inbox reply drafts, item lifecycle stages + Kanban/Timeline, global
  search, CSV import, event analytics, and workspace members/roles. **83 passed / 2 skipped**
  (`test_reports/iteration_10.json`).
- **DJ-deck redesign + Stocksix sync + AI status (Phase 26): COMPLETE** — DJ-deck UI (3D panels,
  glowing buttons, neon accents, equalizer bars), Stocksix inventory connector (wizard + idempotent
  sync via `GET /api/public/v1/inventory`), Integration Hub offline fallback, `GET /api/ai/status`
  probe + AI-status banner + real sidebar AI light. **92 passed / 3 skipped**.
- **Open-source/zero-cost migration: COMPLETE** — LLM defaults to local Ollama (no key, no paid
  API; blank `LLM_BASE_URL` can no longer silently fall back to a paid endpoint), Google Fonts CDN
  removed (self-hosted Inter/Roboto Mono), GitHub Actions CI + GitHub Pages deploy added,
  `docker-compose.yml` for one-machine self-hosting, README/LICENSE added, git repo initialized.
  Backend suite **88 passed / 3 skipped** (skips = live-LLM POCs, opt-in via
  `LISTRIX_RUN_LIVE_LLM_TESTS=1`).
- Preview DB has leftover isolation-test data — safe to purge before demos.

---

## 8. Immediate Next Actions (in order)
1. ✅ **Cleanup done:** `WORKSPACE_CREATED` event fixed; legacy tests relocated to `backend/tests/`;
   purge preview test data still requires preview DB access.
2. ✅ **Backend refactor + DB indexes done** (HANDOVER §23–24) — modular routes/services, isolation
   suite + new local tests as the safety net.
3. ✅ **LLM retry/backoff + caching done** (`services/llm.py`).
4. ✅ **Authentication implemented (staged):** email/password + JWT (`/api/auth/register|login|me`),
   bcrypt hashes, `owner_id` on workspaces, ownership guards on `/workspaces/{id}`, auth-aware
   tenant scoping in `get_wid`, LLM rate limiting, strict enforcement via `AUTH_REQUIRED=true`.
   Remaining: frontend login flow polish (page shipped; header sign-in/out wired), CORS origin
   lockdown for multi-origin exposure, per-workspace usage quotas.
5. ✅ **Real TradeMe connector done** — `services/integrations/trademe.py`: OAuth 1.0a (starts when
   `TRADEME_CONSUMER_KEY`/`TRADEME_CONSUMER_SECRET` are set), Fernet-encrypted tokens at rest,
   callback route `/integrations/{platform}/oauth/callback`, sync → pending suggestions only
   (never auto-post); unconfigured deployments keep the legacy simulated toggle.
6. ✅ **Financials done (Phase 15)** — `services/financials.py` + `GET /api/financials`: fee/tax/
   net/margin math (7.9% marketplace fee, per-workspace currency + tax_rate), value-estimate
   fallback for unlisted items, category aggregation; Financials page shipped (totals + category
   table + top items).
7. ✅ **Sales tracking done (Phase 15b)** — `mark-sold`/`mark-unsold` + `ITEM_SOLD`/`ITEM_UNSOLD`
   events; Financials now reports realized vs potential P&L.
8. ✅ **Object storage + jobs + notifications + scheduler (Phases 16–17)** — `image_blobs` +
   thumbnails; `analyze-all` runs as a pollable job; bell feed; opt-in scheduler.
9. ✅ **Facebook + Gmail connectors + comms hub (Phase 18)** — staged behind env tokens; inbox
   reply drafts; `INBOX_REPLY_DRAFTED` events.
10. ✅ **Workflow engine (Phase 19)** — item stages with validated transitions; Kanban + Timeline.
11. ✅ **Search / CSV import / analytics (Phase 20)** — `GET /api/search`, `/workspaces/import`,
    `GET /api/analytics`.
12. ✅ **Multi-user roles (Phase 21)** — `workspace_members` + owner-gated invite/remove.
13. **Remaining** — live connector validation with real credentials; sales P&L refinements
    (per-sale COGS/payout reconciliation); push/email notification channels.

---

## 9. Known Bugs / Watch-outs
- Invalid/missing `X-Workspace-Id` silently falls back to default for UNAUTHENTICATED requests
  (intentional legacy behavior; authenticated requests are strict — 403 on foreign workspaces).
- Rate limiter is in-process only — multi-worker deployments need a shared store (Redis).
- TradeMe OAuth tokens are encrypted with a Fernet key derived from `JWT_SECRET` unless
  `CONNECTOR_ENCRYPTION_KEY` is set — set it in production so tokens survive restarts.
- TradeMe network calls were verified with mocked HTTP in tests; live behavior needs a real
  TradeMe consumer key/secret + registered callback URL before production use.
- `JWT_SECRET` unset → dev fallback generates a persistent secret at `backend/.jwt_secret`
  (gitignored) so auth tokens survive restarts; production should still set `JWT_SECRET`.
- LLM responses are cached for `LLM_CACHE_TTL` seconds (default 600) — briefs/assistant answers can be up to 10 minutes stale by design; tune or clear via `services.llm.clear_llm_cache()`.
- `/workspaces/{id}` GET/PUT/EXPORT are not ownership-guarded (fine w/o auth; **lock down with auth**).
- Images are compressed client-side (max ~1024px JPEG) before storage/vision, and oversized
  payloads are rejected server-side — this prevents LLM "context length exceeded" errors
  from large base64 photos (raw 5MB photo ≈ 6.7MB base64 ≈ 1.6M tokens).
- `analyze-all` fans out up to 12 concurrent LLM calls (latency/cost on big inventories).
- Voice (Web Speech API) is Chromium-only and not auto-testable.

---

## 10. How to Test After Changes
- **Local (no LLM key / no Mongo needed):** `cd /app/backend && . .venv/bin/activate && pytest`
  — runs the new mongomock-based suites (`tests/test_api.py`, `test_helpers.py`, `test_llm.py`).
- **Against the preview deployment:** `python /app/backend/tests/test_workspace_isolation.py` and
  `python /app/backend/tests/test_workspace_isolation_extended.py` (set `LISTRIX_TEST_BASE_URL` to
  point at a local server with `MONGO_URL=mongomock://` for offline runs). Fix ALL reported issues
  before shipping.
- Manual: curl with different `X-Workspace-Id` headers; confirm no cross-tenant data and no `_id`.
- Frontend: esbuild compile check → screenshots for visual QA.

---

## 11. Product Decisions Locked In (from the owner)
- Verify/harden workspaces FIRST (done, 100%). No major new features until foundation stable.
- **Auth deferred**, but architecture must not block it later.
- **Integrations stay simulated** but production-ready/modular; **TradeMe is the first real one**.
- Maintain a **living** `docs/Listrix_Development_Diary.md`.
- Production-quality only (no mock UI/placeholder screens except deliberate integration architecture).
- After each major task: self-review, improve, document, then proceed.

_End of PROJECT_STATE. Full detail: `/app/docs/HANDOVER.md`._
