# Listrix — Complete Engineering Handover

> **Document status:** Authoritative handover. Produced during the workspace-hardening session.
> **Audience:** A professional software team or AI agent with zero prior context.
> **Read this together with:** `/app/PROJECT_STATE.md` (fast continuation guide) and
> `/app/docs/Listrix_Development_Diary.md` (decision log + roadmap) and
> `/app/docs/ProductionReview.md` (earlier consolidation review).

---

## 1. Executive Summary

**Listrix** is a multi-tenant, AI-powered **Business Operating System for resellers**. It turns raw
inventory (an item name, description, condition, optional photo and cost) into polished, priced
marketplace listings, then acts as a continuous **AI Marketing Manager** that evaluates each
listing, produces confidence-scored recommendations, and applies approved changes.

The product is built as a **control room**: the AI never executes a change or an external action on
its own. Every recommendation is queued, explained (preview + reason + expected impact + confidence
+ risk), and only mutates data after the human clicks **Approve**. This "Control Layer" is a core
product principle, not a feature toggle.

The system is **multi-business**: a single operator can run several isolated businesses
("workspaces"). Every piece of data — items, listings, events, suggestions, performance, briefs,
integrations, inbox — is strictly scoped to a `workspace_id`. Data, AI memory, branding and
connectors are fully isolated per workspace.

**Core value proposition delivered today:**
- AI listing generation (title, description, price, hashtags) — real LLM (local Ollama, open weights).
- Visual Intelligence: photo → item identification, condition, features, value range — real LLM vision (same local model).
- AI Marketing Agent: per-item performance scoring + ranked, approval-gated action suggestions.
- Command Center dashboard: daily AI briefing, live widgets, performance intelligence, event stream.
- Live AI Assistant with browser voice (STT/TTS).
- Smart Inbox, Integration Hub (simulated connectors), Multi-Business Workspaces.

**Tech stack:** FastAPI (Python) + React 19 (CRA/CRACO) + MongoDB (Motor async driver). LLM access
via the public `openai` SDK against **local Ollama** by default (`LLM_BASE_URL` defaults to
`http://localhost:11434/v1`, `LLM_MODEL` defaults to `llama3.2-vision`) — no API key, no paid service.
A different OpenAI-compatible endpoint can be configured, but nothing ships pointing at one.

**Current maturity:** Feature-rich MVP → early commercial product. Multi-tenant isolation has been
verified at 100% (27/27 automated isolation scenarios, zero cross-workspace leakage). No
authentication yet (single-operator assumption). External connectors and market signals are
simulated but architected for real wiring.

---

## 2. Current Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                          Browser (React 19)                        │
│  React Router 7 · TanStack Query 5 · Tailwind + shadcn/ui · sonner │
│                                                                    │
│  WorkspaceProvider (context) ── localStorage: listrix_workspace_id │
│        │                                                           │
│        ▼                                                           │
│  axios instance (lib/api.js) ── request interceptor injects        │
│        X-Workspace-Id header on EVERY call                         │
└─────────────────────────────┬──────────────────────────────────── ┘
                              │  HTTPS, all routes prefixed /api
                              ▼
        ┌───────────────────────────────────────────────┐
        │   Kubernetes Ingress                            │
        │   /api/*  → backend :8001                        │
        │   /*      → frontend :3000                       │
        └───────────────────────┬─────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│                      FastAPI (backend/server.py)                    │
│  APIRouter(prefix="/api") · CORS middleware                         │
│                                                                    │
│  get_wid() dependency ── reads X-Workspace-Id, validates it,        │
│     falls back to the default workspace if missing/invalid          │
│                                                                    │
│  Route groups: workspaces · items/listings/events · vision ·        │
│     marketing agent · suggestions (control layer) · assistant ·     │
│     brief · competitors · integrations · inbox                      │
│                                                                    │
│  Shared services: call_llm() (LlmChat + optional ImageContent),     │
│     extract_json(), log_event(), build_ai_memory()                  │
└───────────────┬───────────────────────────────┬──────────────────┘
                │ Motor (async)                  │ openai SDK
                ▼                                ▼
     ┌────────────────────┐          ┌──────────────────────────────┐
     │ MongoDB (DB_NAME)   │          │ Local Ollama (default)        │
     │ 10 collections,     │          │ → llama3.2-vision (open weights)│
     │ all workspace-scoped│          │   no API key, no paid service │
     └────────────────────┘          └──────────────────────────────┘
```

**Key architectural facts:**
- **Single backend file** today: `backend/server.py` (~1000 lines). Monolithic by design for MVP
  speed; a modular refactor is recommended (see §23).
- **Stateless backend**: no server-side session. Tenant identity is carried per-request via the
  `X-Workspace-Id` HTTP header. This is intentional and forward-compatible with future auth
  (a JWT would simply carry/validate the workspace claim).
- **UUID string identifiers everywhere** (never Mongo ObjectId). All documents use `id: str(uuid4())`
  and Mongo `_id` is always excluded from responses (`{"_id": 0}`).
- **Datetimes** are timezone-aware UTC, stored as ISO-8601 strings, re-parsed on read.
- **All AI output is strict JSON** parsed through one shared `extract_json()` helper (handles code
  fences and stray text).

---

## 3. Folder Structure Explanation

```
/app
├── backend/
│   ├── server.py                # THE backend. All models, routes, AI logic, migration.
│   ├── requirements.txt         # Python deps (pinned). Update via pip install + pip freeze.
│   ├── .env                     # MONGO_URL, DB_NAME, CORS_ORIGINS, LLM_API_KEY (DO NOT rewrite)
│   ├── test_core.py             # POC: text listing generation via LLM (historical, standalone)
│   ├── test_core2.py            # POC: vision + marketing agent (historical, standalone)
│   ├── test_workspace_isolation.py           # Automated isolation regression suite (from testing agent)
│   └── test_workspace_isolation_extended.py  # Extended isolation/mutation-protection suite
│
├── frontend/
│   ├── package.json             # React 19, CRACO, deps. Update via `yarn add` ONLY.
│   ├── craco.config.js          # CRA override (aliases @/ → src/)
│   ├── tailwind.config.js       # Design tokens → Tailwind theme (colors, shadows, fonts, radius)
│   ├── postcss.config.js
│   ├── .env                     # REACT_APP_BACKEND_URL (DO NOT change), WDS_SOCKET_PORT
│   └── src/
│       ├── index.js             # ReactDOM root. Wraps App in QueryClientProvider.
│       ├── index.css            # Global design tokens (CSS variables), dark palette, utilities.
│       ├── App.js               # Router + WorkspaceProvider + AppShell + AIAssistant + Toaster.
│       ├── App.css              # App-level styles.
│       ├── context/
│       │   └── WorkspaceContext.js   # Workspace state, switching, branding injection.
│       ├── lib/
│       │   ├── api.js           # axios instance + interceptor + all endpoint functions.
│       │   ├── queries.js       # TanStack Query hooks + shared cache invalidation.
│       │   ├── derive.js        # Pure presentational helpers (scores, money, insights).
│       │   └── utils.js         # cn() classname helper (shadcn).
│       ├── components/
│       │   ├── layout/
│       │   │   ├── AppShell.js  # Header, mobile drawer, page title map, page container.
│       │   │   └── Sidebar.js   # Desktop nav + WorkspaceSwitcher + model-status footer.
│       │   ├── WorkspaceSwitcher.js   # Switch/create workspace dropdown.
│       │   ├── AIAssistant.js   # Floating assistant panel + Web Speech API voice.
│       │   ├── ControlActionDialog.js # Approval modal (the Control Layer UI).
│       │   ├── ActionCard.js    # A queued suggestion card (approve/reject).
│       │   ├── AIInsightCard.js # Derived insight card.
│       │   ├── DailyBriefing.js # Daily AI briefing panel.
│       │   ├── EventTimeline.js # Color-coded event stream (25+ event types).
│       │   ├── ItemCard.js      # Inventory item card.
│       │   ├── PerformanceIntelligence.js # Best/worst/needs-attention panel.
│       │   ├── StatCard.js      # KPI stat tile.
│       │   └── WidgetCarousel.js# Auto-rotating dashboard widgets.
│       ├── pages/
│       │   ├── Dashboard.js     # "Command Center".
│       │   ├── Items.js         # Inventory grid.
│       │   ├── ItemDetail.js    # Per-item insight panel (vision, perf, price history, competitors).
│       │   ├── Workflows.js     # 4-step create → vision → generate → review wizard.
│       │   ├── AIManager.js     # Action Queue + performance table + control approvals.
│       │   ├── Market.js        # Generated listings gallery (copy-to-clipboard).
│       │   ├── Inbox.js         # Smart operations inbox.
│       │   ├── IntegrationHub.js# Connector cards (connect/sync).
│       │   ├── AIControl.js     # Model status + full event log.
│       │   └── Settings.js      # Workspace config (branding, AI prefs, business, export).
│       └── components/ui/        # shadcn/ui primitives (accordion…tooltip).
│
├── docs/
│   ├── HANDOVER.md              # ← THIS FILE.
│   ├── Listrix_Development_Diary.md  # Living decision log + roadmap.
│   └── ProductionReview.md      # Earlier consolidation review.
│
├── plan.md                      # Phase-based development plan (source of truth for progress).
├── PROJECT_STATE.md             # Fast-start continuation file for the next engineer/agent.
└── test_reports/
    └── iteration_1..4.json       # Testing-agent reports (iteration_4 = workspace isolation, 100%).
```

---

## 4. Database Schema and Relationships

MongoDB database name comes from `DB_NAME`. **Every collection except `workspaces` is
workspace-scoped** via a `workspace_id` field. All identifiers are UUID strings.

### Collections (10 scoped + 1 root)

**`workspaces`** (root / tenant registry)
```
id: str (uuid)              # tenant id, referenced by every other collection
name: str
logo: str|null              # base64 data URL
primary_color: str          # hex, default #FF7A1A (drives branding)
secondary_color: str        # hex, default #3B82F6
contact_email, contact_phone, website: str|null
marketplace_accounts: [str]
tax_rate: float|null
currency: str = "USD"
timezone: str = "UTC"
business_type: str = "Reseller"
ai_preferences: {           # per-workspace AI personalization
  writing_style, pricing_behavior, selling_strategy, customer_comms_style
}
ai_memory: {}               # reserved for future persisted memory
is_default: bool            # exactly one workspace is the fallback default
created_at: ISO-8601 str
```

**`items`** — inventory
```
id, workspace_id, name, description, condition
image: str|null (base64)    # NOTE: stored inline (see tech debt §22)
cost: float|null
category: str|null
vision: {item_type, category, brand, condition_guess, features[]}|null
value_estimate: {low, mid, high, confidence, reasoning}|null
market_signal: {...}        # written by analyze_one (simulated, deterministic)
listed_at: ISO str|null
times_relisted: int = 0
created_at
```

**`listings`** — AI-generated marketplace copy
```
id, workspace_id
item_id: str|null           # → items.id (soft FK; also matched by source_name)
source_name: str            # item name at generation time (fallback join key)
listing_title, listing_description: str
suggested_price: float
hashtags: [str]
created_at
```

**`events`** — immutable activity log (the event system, see §7)
```
id, workspace_id, type: str, message: str, payload: any|null, created_at
```

**`performance`** — per-item marketing scoring (one doc per item, upserted)
```
workspace_id, item_id, item_name
status: "good"|"average"|"poor"
likelihood_of_sale: float (0-100)
reason, recommended_action: str
time_on_market_hours: float
updated_at
```

**`suggestions`** — the Action Queue (control layer)
```
id, workspace_id, item_id, item_name, listing_id|null
type: one of reduce_price|improve_title|add_keywords|relist|add_urgency|generate_listing
title, detail, reason, expected_impact, expected_outcome
confidence: float
risk_level: low|medium|high
params: {}                  # type-specific action params (e.g. {new_price})
status: pending|applied|dismissed
created_at, applied_at|null, dismissed_at|null
```

**`price_history`** — audit of price changes
```
id, workspace_id, item_id, listing_id, old_price, new_price, reason, created_at
```

**`briefs`** — daily AI briefings
```
id, workspace_id, headline, summary, what_sold, what_didnt_sell,
priority_items[], suggested_actions[], risk_alerts[], opportunities[], created_at
```

**`feedback`** — closed learning loop (approved/rejected outcomes)
```
id, workspace_id, suggestion_id, item_id, type, action(approved|rejected), outcome, created_at
```

**`integrations`** — connector state (seeded per workspace from DEFAULT_CONNECTORS)
```
workspace_id, platform, kind(marketplace|communication|data),
auth_status(connected|disconnected), permissions[], sync_enabled: bool, last_sync: ISO|null
```

**`inbox`** — smart operations inbox messages (regenerated on refresh)
```
id, workspace_id, type(AI_ALERT|OPPORTUNITY|ACTION_RECOMMENDED|BUYER_MESSAGE|SYSTEM),
priority(high|medium|low), title, body, suggested_action,
related_item_id, related_item_name, read: bool, simulated?: bool, created_at
```

### Relationships (soft foreign keys; no DB constraints — enforced in code)
```
workspaces.id  1───N  items.workspace_id (and every other collection)
items.id       1───N  listings.item_id            (also joined by listings.source_name == items.name)
items.id       1───1  performance.item_id         (upserted)
items.id       1───N  suggestions.item_id
items.id       1───N  price_history.item_id
suggestions.id 1───1  feedback.suggestion_id
```
**No indexes are currently defined** beyond Mongo's default `_id`. See §24 for the recommended index set.

---

## 5. API Endpoints and Purpose

Base URL: `${REACT_APP_BACKEND_URL}/api`. Unless noted, endpoints depend on `get_wid` and are
scoped by the `X-Workspace-Id` header. All list/detail responses exclude Mongo `_id`.

### Health / Workspaces
| Method | Path | Purpose | Scoped |
|---|---|---|---|
| GET | `/` | Health check (`{message: "Listrix API is running"}`) | — |
| GET | `/workspaces` | List all workspaces (ensures a default exists) | No (registry) |
| POST | `/workspaces` | Create workspace + seed 5 connectors | No |
| GET | `/workspaces/{ws_id}` | Fetch one workspace | By path id |
| PUT | `/workspaces/{ws_id}` | Update workspace fields (branding, AI prefs, business) | By path id |
| GET | `/workspaces/{ws_id}/export` | Full JSON snapshot of a workspace's data | By path id |

> **Security note:** the `{ws_id}` routes take the id from the path, not the header, and are not
> guarded by ownership (no auth yet). Acceptable for single-operator today; **must be locked down
> when auth lands** (see §11, §25).

### Items / Listings / Events
| Method | Path | Purpose |
|---|---|---|
| POST | `/items` | Create item (logs `ITEM_CREATED`) |
| GET | `/items?limit=100` | List items (newest first) |
| GET | `/items/{item_id}` | Fetch item (404 if not in workspace → isolation) |
| POST | `/ai/generate` | LLM: generate + persist a listing (logs `LISTING_GENERATED`) |
| GET | `/listings?limit=100` | List generated listings |
| GET | `/events?limit=100` | Activity log (newest first) |
| POST | `/client-events` | Whitelisted UI telemetry (`WIDGET_VIEWED`, `VOICE_QUERY_RECEIVED`, `USER_APPROVED_ACTION`, `COMMAND_CENTER_OPENED`) |

### Vision
| POST | `/ai/vision/analyze` | LLM vision: base64 image → identification + value estimate; if `item_id` given, persists vision to that item. Logs `IMAGE_ANALYSED`, `VALUE_ESTIMATED`. |

### Marketing Agent
| POST | `/ai/analyze/{item_id}` | Analyze one item → performance + suggestions |
| POST | `/ai/analyze-all?limit=12` | Batch analyze (concurrent, capped) |
| GET | `/performance` | All performance rows |
| GET | `/performance-intelligence` | Aggregated best/worst/needs-attention, next actions, revenue opportunity |
| GET | `/market/signals` | Per-item simulated market signals |
| GET | `/price-history/{item_id}` | Price change history |
| GET | `/competitors/{item_id}` | Simulated competitor positioning (structure only) |

### Control Layer (Action Queue)
| GET | `/suggestions?status=&item_id=` | List suggestions (sorted by confidence) |
| POST | `/suggestions/{id}/apply` | **Approve & apply** (mutates listing/item per type). Logs `USER_APPROVED_ACTION`, `ACTION_APPROVED`, `AI_SUGGESTION_APPLIED`. Only `pending` allowed. |
| POST | `/suggestions/{id}/dismiss` | Reject (feeds learning loop) |
| POST | `/suggestions/{id}/edit` | Modify a pending suggestion's detail/params before approval |

### Assistant / Brief
| POST | `/ai/assistant` | Spoken-style answer + recommendation cards (voice flag logs voice events) |
| POST | `/brief/generate` | Generate + persist daily briefing |
| GET | `/brief/latest` | Most recent briefing (or null) |

### Integrations (simulated, modular)
| GET | `/integrations` | List connectors (seeds defaults if empty) |
| POST | `/integrations/{platform}/connect` | Toggle connected/disconnected |
| POST | `/integrations/{platform}/sync` | Simulated sync (requires connected); logs sync events |

### Inbox (simulated)
| POST | `/inbox/refresh` | Regenerate inbox messages from current perf/suggestions/items |
| GET | `/inbox` | List messages sorted by priority |

---

## 6. AI Systems and How They Interact

All AI runs through **one shared function**, `call_llm(system_message, prompt, image_b64=None)`:
- Uses `services.llm.call_llm(system_message, prompt, image_b64=None)` backed by the OpenAI-compatible SDK
  pointed at local Ollama by default (see §27).
- Sends a `UserMessage`; attaches `ImageContent(image_base64=...)` when an image is provided (vision).
- Every system prompt ends with *"respond with a single valid JSON object and nothing else"*, and
  the response is parsed by `extract_json()` (strips ``` fences, isolates the outermost `{...}`).

There are **five AI subsystems**, each a distinct system prompt + prompt builder:

1. **Listing Generator** (`LISTING_SYSTEM`, `generate_listing_ai`)
   - Input: item name/description/condition/cost + workspace AI memory.
   - Output: `listing_title` (≤80 chars), `listing_description`, `suggested_price`, `hashtags[]`.

2. **Visual Intelligence** (`VISION_SYSTEM`, `build_vision_prompt`)
   - Input: base64 image + optional seller hint.
   - Output: item_type, category, brand, condition_guess, features[], suggested title/description/price,
     `value_estimate{low,mid,high,confidence,reasoning}`, market_positioning.
   - Side effect: if called with `item_id`, persists vision + value estimate onto the item.

3. **Marketing Intelligence Agent** (`AGENT_SYSTEM`, `build_agent_prompt`, orchestrated by `analyze_one`)
   - Input: item, its latest listing, gathered memory (time-on-market, price changes, applied/dismissed
     suggestion types), workspace AI memory, and simulated market signal + lifecycle.
   - Output: `performance{status,likelihood_of_sale,reason,recommended_action}` +
     `suggestions[]` (2–4 ranked, each typed with params, confidence, expected impact/outcome, risk).
   - Guardrails: never repeats dismissed suggestion types; if no listing exists, top suggestion must be
     `generate_listing`; only whitelisted `SUGGESTION_TYPES` are persisted.

4. **Live Assistant** (`ASSISTANT_SYSTEM`)
   - Input: owner's question + workspace-scoped business context (per-item or business-wide) + AI memory.
   - Output: short spoken-style `answer` + up to 5 `recommendations{title,detail,urgency,confidence}`.
   - Explicitly told it NEVER executes changes — only recommends.

5. **Daily Briefing** (`BRIEF_SYSTEM`)
   - Input: aggregate stats (item/listing counts, items without listings, poor/good performers,
     pending/applied counts, avg price) + AI memory.
   - Output: headline, summary, what_sold, what_didnt_sell, priority_items, suggested_actions,
     risk_alerts, opportunities.

### The unifying concept: per-workspace AI memory
`build_ai_memory(wid)` assembles a personalization block from the workspace's `ai_preferences`
plus derived behavior (frequent categories, which suggestion types the business tends to apply vs
reject). `memory_block(mem)` renders it as a prompt preamble injected into **all five** subsystems,
so each business gets AI behavior tuned to itself. This memory is strictly workspace-scoped.

### Interaction flow (typical)
```
Workflow wizard → vision/analyze (autofill) → items.create → ai/generate (listing)
     → ai/analyze/{id} (performance + suggestions)
     → suggestions appear in Action Queue / Inbox / Dashboard widgets
     → user approves via ControlActionDialog → suggestions/{id}/apply mutates listing/item
     → feedback recorded → future analyze_one avoids repeating dismissed types
     → every step emits events → EventTimeline + AIControl + Dashboard activity
```

---

## 7. Event System Architecture

The event log is the backbone of observability and the activity UI.

- **Write path:** `log_event(wid, type, message, payload=None)` inserts an `Event` doc
  (uuid, workspace_id, type, message, payload, created_at ISO). It is wrapped in try/except so a
  logging failure never breaks the primary request. Almost every meaningful action logs one or more
  events.
- **Read path:** `GET /api/events` (scoped, newest-first). Rendered by `EventTimeline.js`, which maps
  each `type` to a color + lucide icon + human label via `TYPE_META`.
- **Client-originated events:** `POST /api/client-events` accepts only a whitelist
  (`CLIENT_EVENT_TYPES`): `WIDGET_VIEWED`, `VOICE_QUERY_RECEIVED`, `USER_APPROVED_ACTION`,
  `COMMAND_CENTER_OPENED`. This prevents arbitrary event injection from the browser.
- **Event taxonomy (25+ types)** includes: `ITEM_CREATED`, `LISTING_GENERATED`, `PRICE_UPDATED`,
  `IMAGE_ANALYSED`, `VALUE_ESTIMATED`, `MARKET_SIGNAL_UPDATED`, `LISTING_VIEW_ESTIMATED`,
  `LISTING_PERFORMANCE_UPDATED`, `AI_SUGGESTION_CREATED`, `ACTION_QUEUED`, `USER_APPROVED_ACTION`,
  `ACTION_APPROVED`, `AI_SUGGESTION_APPLIED`, `ACTION_REJECTED`, `AI_BRIEFING_GENERATED`,
  `DAILY_BRIEF_GENERATED`, `PERFORMANCE_RECALCULATED`, `MARKET_MATCH_FOUND`,
  `CONNECTOR_AUTH_SUCCESS`, `CONNECTOR_SYNC_EXECUTED`, `EXTERNAL_DATA_RECEIVED`,
  `SYNC_ACTION_QUEUED`, `INBOX_MESSAGE_RECEIVED`, `VOICE_QUERY_RECEIVED`,
  `VOICE_QUERY_PROCESSED`, `AI_ERROR`.
- **Design intent:** events are an append-only audit trail. They are the primary substrate for a
  future analytics/notifications layer and for compliance/audit once auth exists.
- **Known cleanup:** `create_workspace` currently logs an `ITEM_CREATED` event for a workspace
  creation (semantically wrong; should be `WORKSPACE_CREATED`). Low priority. See §21/§23.

---

## 8. Workflow Engine Design

The "workflow engine" today is a **guided 4-step creation wizard** (`pages/Workflows.js`), not a
generalized state machine. Steps:

1. **Item Details** — name, description, condition (select), category. Client validation requires
   name/description/condition.
2. **Photo & AI Vision** — upload image (≤5MB, image/* only, read as base64 data URL) → optional
   "Analyze Image & Auto-Fill" calls `vision/analyze` and pre-fills fields (user can override). Also
   captures optional cost.
3. **Generate** — review summary, then `Save & Generate`: creates the item (persisting vision +
   value estimate) then immediately calls `ai/generate` for the listing.
4. **Review** — shows the generated listing (title, description, price, hashtags) with CTAs to the
   AI Manager or to create another.

**Design characteristics:** linear stepper with progress bar; per-step validation; React Query
mutations (`useCreateItem`, `useGenerateListing`) that invalidate all caches on success so every
surface updates. It is intentionally simple. The roadmap calls for a true workflow engine
(Kanban / Calendar / Timeline views, item lifecycle states) — see §20/§32.

---

## 9. Marketing Intelligence Architecture

The Marketing Intelligence Agent is the product's differentiator. It behaves like a marketing
manager, not a chatbot.

**Pipeline (`analyze_one(wid, item)`):**
1. Find the item's latest listing (by `item_id` or `source_name`).
2. `gather_memory` — time-on-market, count of price changes, applied/dismissed suggestion types (per item).
3. `build_ai_memory` — workspace-level preferences + behavior.
4. `simulate_market_signal(item)` (deterministic via md5 seed of item id) → demand/competition/
   saturation/price-trend; `simulate_lifecycle(listing, perf)` → views/engagement/conversion.
5. Persist the market signal on the item; log `MARKET_SIGNAL_UPDATED` (+ `LISTING_VIEW_ESTIMATED`).
6. `call_llm(AGENT_SYSTEM, build_agent_prompt(...))` → structured performance + suggestions.
7. Upsert `performance` (one row per item); log `LISTING_PERFORMANCE_UPDATED`.
8. Replace this item's **pending** suggestions with the new ranked set (validated against
   `SUGGESTION_TYPES`); log `ACTION_QUEUED` + `AI_SUGGESTION_CREATED`.

**Batch:** `analyze-all` runs `analyze_one` concurrently with `asyncio.gather`, capped at `limit`
(default 12), each wrapped so one failure doesn't abort the batch.

**Aggregation:** `performance-intelligence` computes best/worst/needs-attention lists, the next
recommended actions (top pending by confidence), and a naive `predicted_revenue_opportunity`
(sum of listing price − cost, else value_estimate.mid).

**Closed learning loop:** approvals/rejections write to `feedback` and are surfaced back into the
agent prompt (applied vs dismissed types), so the agent adapts and avoids repeating rejected ideas.

**Important honesty caveat:** there is **no real sales/conversion data**. "Likelihood of sale",
market signals and lifecycle are inferred/simulated. This is by design for the MVP and must be
replaced by real marketplace data via the Integration Hub.

---

## 10. Multi-Business Workspace Implementation

This is the hardened foundation of the product.

**Backend enforcement:**
- `get_wid(x_workspace_id: Header)` — validates the header against the `workspaces` collection.
  If present & valid → returns it. If missing/invalid → `ensure_default_workspace()` returns the
  default workspace id (safe fallback; see edge-case note below).
- Every scoped route declares `wid: str = Depends(get_wid)` and includes `workspace_id: wid` in
  **both** query filters and inserts. Detail/mutation routes match on `{id, workspace_id}` so a
  foreign id returns **404** (proven in tests), never another tenant's data.
- `ensure_default_workspace()` runs on startup and lazily: creates a default workspace if none
  exists and **migrates any legacy unscoped documents** into it (`{workspace_id: {$exists: False}}`
  → default id) across all `SCOPED` collections.
- New workspaces are seeded with the 5 default connectors (`DEFAULT_CONNECTORS`).

**Frontend enforcement:**
- `lib/api.js` axios request interceptor injects `X-Workspace-Id` from
  `localStorage["listrix_workspace_id"]` on every request.
- `WorkspaceContext` loads workspaces, picks the saved/default/first as `current`, persists the id,
  and injects branding CSS variables (`applyBranding` maps the workspace's hex `primary_color` →
  HSL and overrides `--primary/--accent/--ring`).
- `switchWorkspace(id)` updates localStorage + current + branding, then
  `queryClient.invalidateQueries()` (all keys) so every panel refetches under the new tenant.
- `WorkspaceSwitcher` allows switching and creating workspaces; `Settings` edits the current one.

**Verification (this session):** automated testing agent ran **27/27 isolation scenarios at 100%**
(read isolation across all list endpoints; cross-workspace mutation protection returning 404/empty;
header edge cases; integration isolation). **Zero cross-workspace leakage.** Report:
`/app/test_reports/iteration_4.json`. Regression suites saved at
`backend/tests/test_workspace_isolation.py` and `..._extended.py`.

**Edge-case behavior (documented, intentional):** an invalid/missing header silently falls back to
the default workspace rather than erroring. This is UX-safe with no auth. Once auth exists,
consider a strict mode that rejects unknown workspace ids for the authenticated user.

---

## 11. Security Architecture

**Current posture (be explicit): the app has NO authentication or authorization yet.** It assumes a
single trusted operator. What exists:

- **Tenant isolation** at the data layer (workspace scoping) — verified, strong.
- **Control Layer** — the AI cannot mutate data or perform external actions without an explicit
  human approve action; approvals are logged.
- **Event whitelist** on `/client-events` prevents arbitrary client event injection.
- **Secrets** live only in `backend/.env` (server-side); never shipped to the client. The frontend
  only knows `REACT_APP_BACKEND_URL`.
- **CORS** is configured from `CORS_ORIGINS` (currently permissive `*` for preview).
- **Input validation** via Pydantic models with field validators (non-empty name/description/
  condition; non-negative cost).

**Gaps / risks (must address before real production):**
1. **No authentication** — anyone with the URL can use the API. This is the #1 blocker for real
   multi-user/production use.
2. **`/workspaces/{ws_id}` GET/PUT/EXPORT are not ownership-guarded** — with the id, any workspace
   can be read/updated/exported. Fine for single operator; a cross-tenant leak once multi-user.
3. **base64 images inline** — large payloads; no malware/type deep-validation beyond MIME prefix.
4. **CORS `*`** — tighten to known origins in production.
5. **No rate limiting / abuse protection** on LLM endpoints (cost + DoS risk).
See §25 for the recommended security roadmap. The stack already ships auth-ready libs
(`pyjwt`, `bcrypt`, `passlib`, `python-jose`) in requirements.

---

## 12. UI/UX Philosophy

- **"Operations control room," not a form app.** The interface is designed to feel like a cockpit:
  dense but scannable, dark, with an always-present activity stream and a live assistant.
- **Human-in-the-loop is visible.** The Control Layer is a first-class UI concept — the approval
  dialog explicitly shows preview, explanation, expected impact, confidence and risk before any
  change. Trust is built by never surprising the user.
- **Real data only.** Derived metrics (`lib/derive.js`) are computed from actual items/listings;
  simulated data is always labeled `(simulated)`.
- **Every meaningful element has a `data-testid`** (kebab-case, role-based) for stable automation.
- **Explicit data states** everywhere: loading (spinners/skeletons), empty (helpful CTA), error
  (toast + retry).
- **Responsive**: desktop sidebar collapses to a mobile drawer; the assistant is a floating panel.
- **Accessibility**: semantic buttons, focus/hover/disabled states, aria labels on icon buttons.

---

## 13. Design System and Branding Rules

**Theme:** Dark industrial — charcoal surfaces + industrial orange accent.

**Tokens (defined in `src/index.css` as HSL CSS variables, consumed via Tailwind theme in
`tailwind.config.js`):**
- Surfaces: `--background 220 18% 6%`, `--card 220 16% 9%`, `--muted 220 12% 14%`, layered
  `--lx-surface-0..3`.
- Primary/accent: `--primary/--accent/--ring 24 95% 55%` (industrial orange, `#FF7A1A`).
- Semantic accents: `--lx-orange`, `--lx-blue (210 85% 60%)`, `--lx-green (145 62% 48%)`,
  `--lx-purple (270 65% 62%)`, `--destructive (0 72% 52%)`.
- Radius: `--radius: 0.75rem`.
- Shadows/glows (Tailwind): `panel`, `panelSoft`, `orangeGlow`, `orangeGlowStrong`.
- Texture: `.lx-noise` subtle dot-grid overlay; `.lx-scroll` thin dark scrollbars.

**Typography:** Inter (sans) + Roboto Mono (mono, for status/technical), loaded from Google Fonts.

**Per-workspace branding:** each workspace's `primary_color` (hex) is converted to HSL at runtime
and injected over `--primary/--accent/--ring` by `applyBranding()`, so the whole UI re-skins per
business. Logo appears in the sidebar and switcher.

**Rules for contributors:**
- Never hard-code colors; always use tokens / Tailwind theme classes.
- Use shadcn/ui primitives from `@/components/ui` before hand-rolling.
- Gradients used sparingly (glows/hero only). Icons only from `lucide-react`.
- Keep the app **not** globally center-aligned; grid/flex layouts with generous spacing.
- Toasts via `sonner` (dark theme, richColors), consistent with the palette.

---

## 14. Integration Hub Architecture

**Purpose:** a modular connector layer for marketplaces/communication/data sources. **All connectors
are simulated (structure-only) today** — no real external API calls — but the shape is built for real
wiring with minimal change.

- **Seeding:** `DEFAULT_CONNECTORS` = TradeMe, Facebook Marketplace, Gmail, Pricing Signals,
  Competitor Listings — each with `kind`, `permissions[]`, `auth_status`, `sync_enabled`. Seeded per
  workspace on creation and lazily via `seed_connectors(wid)`.
- **Endpoints:** `GET /integrations` (list), `POST /integrations/{platform}/connect` (toggle
  auth_status), `POST /integrations/{platform}/sync` (requires connected; simulates receiving data
  and queues approval-gated actions; logs `CONNECTOR_SYNC_EXECUTED`, `EXTERNAL_DATA_RECEIVED`,
  `SYNC_ACTION_QUEUED`).
- **UI:** `IntegrationHub.js` renders connector cards with status, permissions, last-sync, and
  connect/sync buttons; a prominent banner states it is structure-only and approval-gated.
- **Design intent for real wiring (TradeMe first):** replace the simulated connect with an OAuth
  flow, store tokens server-side (encrypted; libs already present), and replace `sync` with real API
  pulls that create **pending suggestions** (never auto-posts). The approval + event flow already
  exists, so going live means implementing the provider adapter behind the same endpoints.

---

## 15. Voice System Architecture

- **Fully client-side** using the browser **Web Speech API** (no server audio processing):
  - **STT:** `webkitSpeechRecognition`/`SpeechRecognition` (en-US) captures a query; on result it
    calls the assistant with `voice: true`.
  - **TTS:** `SpeechSynthesisUtterance` speaks the assistant's answer back.
- **Backend involvement:** `POST /ai/assistant` with `voice=true` logs `VOICE_QUERY_RECEIVED` and
  `VOICE_QUERY_PROCESSED` events; otherwise identical to text.
- **UI:** the floating `AIAssistant` panel shows a mic button only if the browser supports speech;
  listening state animates; each AI message has a "Play" (TTS) affordance.
- **Caveats:** best in Chromium; not testable by automated agents; no wake-word/continuous mode.

---

## 16. Widget Architecture

- `WidgetCarousel.js` builds up to three widgets from real data passed in as props
  (`items`, `suggestions`, `perfIntel`): **Item Spotlight**, **AI Recommendation**, **Market
  Summary**.
- Auto-rotates every 8s (interval cleared on unmount); manual prev/next + dot indicators.
- Logs a `WIDGET_VIEWED` client event on mount.
- Rendered on the Dashboard/Command Center. Intentionally lightweight and presentational — a
  foundation for a future configurable widget/mobile surface.

---

## 17. Current Project Status

- **Overall:** stable, feature-rich MVP with a hardened multi-tenant core. Preview app runs; all
  services healthy under supervisor (backend, frontend, mongodb).
- **Multi-workspace isolation:** VERIFIED (100%, 27/27 automated scenarios, zero leakage).
- **Core AI flows:** working against a real LLM — local Ollama by default (listing, vision, agent, assistant, brief).
- **Auth:** none (deferred by explicit product decision; design is auth-ready).
- **Integrations & market signals:** simulated by design.
- **Data currently in DB (preview):** ~7 workspaces, 12 items, 8 listings, 163 events, 30
  suggestions, 8 performance rows, 22 inbox, 35 integrations, 3 briefs (includes test data from
  isolation runs — safe to purge).

---

## 18. Completed Features

- Item CRUD (create/list/detail) with image + cost + category, workspace-scoped.
- AI listing generation (title/description/price/hashtags), persisted.
- Visual Intelligence (image → identification + value estimate) with workflow auto-fill.
- Marketing Intelligence Agent (per-item performance + ranked, typed suggestions).
- Control Layer approval dialog + Action Queue (apply/dismiss/edit), with real listing mutations
  (reduce_price, improve_title, add_keywords, add_urgency, relist, generate_listing).
- Closed feedback learning loop (applied/dismissed history influences future analysis).
- Performance Intelligence aggregation + revenue-opportunity estimate.
- Command Center dashboard (daily briefing, widgets, intelligence, recent items, event stream).
- Live AI Assistant with text + browser voice (STT/TTS), approval-gated.
- Smart Inbox (alerts/opportunities/recommended actions/simulated buyer messages).
- Integration Hub (simulated connectors, connect/sync, event logging).
- Multi-Business Workspaces with full data + AI-memory + branding isolation (VERIFIED).
- Unified event system + color-coded timeline (25+ types).
- Workspace Settings (branding, AI preferences, business profile, JSON export).
- Dark industrial design system with per-workspace re-skinning.

---

## 19. Partially Completed Features

- **Integration Hub connectors** — architecture complete; real OAuth/API calls not implemented
  (simulated). Ready for TradeMe-first wiring.
- **Market signals & listing lifecycle** — deterministic simulation; needs real marketplace data.
- **Competitor intelligence** (`/competitors/{id}`) — structure/positioning logic only; no scraping.
- **Settings tabs** — Branding/AI/Business/Backup are functional; Notifications/Team/Security are
  informational placeholders (roadmap).
- **Production consolidation/refactor** (Phase 9) — partially done; monolith split still pending.
- **Development Diary** — created this session; intended as a living document.

---

## 20. Planned Future Features

- Real authentication, user roles & permissions (P0 for production).
- Real marketplace connectors (TradeMe → Facebook → Gmail) behind the existing approval flow.
- Financials: profit tracking, fees, taxes, margin reporting (schema hooks: cost, tax_rate, currency).
- Unified communications hub for buyer messages/emails (Inbox → real threads).
- Real engagement/sales ingestion to replace simulated signals.
- Global search across inventory/listings/customers/events/reports.
- Workflow engine upgrade: Kanban / Calendar / Timeline + item lifecycle states.
- Scheduled background analysis + push notifications.
- Workspace export/import (export exists; import pending).
- LLM retry/backoff + response caching (cost/latency).

---

## 21. Known Bugs

No functional blockers known. Minor/cosmetic:
1. **Semantic event mislabel:** `create_workspace` logs `ITEM_CREATED` for workspace creation
   (should be `WORKSPACE_CREATED`). Cosmetic in the timeline.
2. **Invalid workspace header** silently falls back to default (intentional, but could mask a
   client bug where the wrong/blank id is sent).
3. **Floating AI assistant button** overlap on very small screens vs the header —
   flagged historically; needs a responsive-position pass (frontend-only).
4. **`analyze-all` LLM concurrency** (cap 12) can spike latency/cost on larger inventories.
5. Preview DB contains leftover isolation-test workspaces/items — purge before demos.

---

## 22. Technical Debt

- **Monolithic `server.py`** (~1000 lines): all models, prompts, routes, migration in one file.
  Hard to test/scale. → Split into routers/services (see §23).
- **Images stored as base64 inline** on `items`/`workspaces` (logo). Bloats documents and list
  payloads. Some list endpoints already project out `image`, but `GET /items` returns it. → Move to
  object storage; store URLs.
- **No DB indexes** beyond `_id`. All queries filter by `workspace_id` (+ item_id/status/created_at)
  → add compound indexes.
- **LLM resilience added (Phase 12):** `services/llm.py` now retries transient failures with
  exponential backoff (default 3 attempts) and caches identical text prompts (TTL 600s; vision
  never cached). Tunable via `LLM_MAX_RETRIES`, `LLM_RETRY_BASE_DELAY`, `LLM_CACHE_TTL`.
- **Soft foreign keys** with dual listing-join (`item_id` OR `source_name`): brittle if item names
  collide/change. → Prefer `item_id` and backfill.
- **Test scripts live in `backend/tests/`** (`test_core*.py`, `test_workspace_isolation*.py`,
  plus new mongomock-based local suites) — relocated during the Phase 12 refactor; legacy suites
  carry skip guards so a plain `pytest` run is fully local (40 tests, mocked LLM).
- **Startup migration** scans all scoped collections on every boot via `ensure_default_workspace`
  fallback path; fine now, but should become an explicit, idempotent migration step.

---

## 23. Recommended Refactoring — ✅ DONE (Phase 12)

This layout is now implemented (route parity 33/33, zero behavior change):
```
backend/
├── server.py                 # app factory, middleware, router include, startup/shutdown
├── config.py                 # constants + env (LLM tuning, connectors, event whitelist)
├── deps.py                   # get_wid, db handle (mongomock:// support for local tests)
├── utils.py                  # pure helpers (parse_iso, to_dt, hours_since, _seed)
├── db/
│   ├── indexes.py            # ensure_indexes() on startup
│   └── migrations.py         # ensure_default_workspace + legacy migration (idempotent)
├── models/                   # Pydantic models grouped by domain (workspace/item/event/agent/ai)
├── services/
│   ├── llm.py                # call_llm + extract_json + retry/backoff + cache
│   ├── events.py             # typed EventType enum + log_event
│   ├── memory.py             # build_ai_memory, memory_block
│   ├── listing.py            # generate_listing_ai
│   ├── vision.py             # vision prompt/parse
│   ├── marketing_agent.py    # analyze_one, gather_memory, simulate_*
│   └── integrations/         # base.py connector-adapter seam (TradeMe wiring = next task)
└── routes/
    ├── workspaces.py items.py listings.py events.py vision.py
    ├── agent.py suggestions.py assistant.py brief.py
    └── integrations.py inbox.py (competitors live in agent.py)
```
Also delivered: typed `EventType` enum; `WORKSPACE_CREATED` event fixed; unit + integration tests
per service under `backend/tests/` (40 passing locally with mongomock + mocked LLM); isolation
regression suites retained as the safety net. Remaining from this section: a shared `scoped_query`
helper (deferred — scoping is already centralized through `get_wid` + route conventions).

---

## 24. Performance Bottlenecks

- **LLM latency dominates** every AI endpoint (seconds per call). Mitigate with: streaming UX,
  caching, and moving `analyze-all` to a background queue.
- **`analyze-all` fan-out** (up to 12 concurrent LLM calls) — bound by provider rate limits; batch
  or queue for larger inventories.
- **base64 image payloads** inflate `GET /items` and item docs → object storage + thumbnails.
- **Indexes applied on startup** (`db/indexes.py`, HANDOVER §23). Set:
  ```
  items:        {workspace_id:1, created_at:-1}
  listings:     {workspace_id:1, item_id:1}, {workspace_id:1, created_at:-1}
  events:       {workspace_id:1, created_at:-1}
  suggestions:  {workspace_id:1, status:1, confidence:-1}, {workspace_id:1, item_id:1}
  performance:  {workspace_id:1, item_id:1}
  price_history:{workspace_id:1, item_id:1, created_at:-1}
  integrations: {workspace_id:1, platform:1}
  inbox:        {workspace_id:1, priority:1}
  workspaces:   {id:1}, {is_default:1}
  ```
- **`invalidateQueries()` on switch** refetches everything — fine now; consider targeted
  invalidation + query keys namespaced by workspace id at scale.

---

## 25. Security Recommendations — Auth implemented (staged rollout)

1. ✅ **Authentication implemented** (email/password + JWT HS256 via `pyjwt`/`bcrypt`):
   `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`; `users` collection with
   bcrypt hashes; `owner_id` attached to workspaces (register creates an owned default workspace).
   Enforced via `get_current_user`/`get_optional_user` deps (`services/auth.py`). Staged rollout:
   `AUTH_REQUIRED=false` (default) keeps the pre-auth single-operator behavior with auth fully
   functional; `AUTH_REQUIRED=true` locks every `/api` route behind a JWT (401 without token).
   Set `JWT_SECRET` + `JWT_TTL_SECONDS` (default 24h) in env.
2. ✅ **`/workspaces/{ws_id}` guarded by ownership**: authenticated users get 403 on other users'
   workspaces (GET/PUT/export); ownerless legacy workspaces remain open in grace mode and are
   blocked in strict mode.
3. ✅ **Tenant derived from JWT + validated header**: `get_wid` now resolves the authenticated
   user's default workspace when no header is sent, and rejects (403) a header workspace not owned
   by the user. No-header/invalid-header silent fallback remains only for unauthenticated requests.
4. ⚠️ **CORS** stays env-driven (`CORS_ORIGINS`); the default `*` is safe only because the app is
   served same-origin behind the ingress — lock to known origins before multi-origin exposure.
5. ✅ **Rate limiting**: in-process sliding window on all LLM endpoints (default 30 calls/min per
   workspace, `LLM_RATE_LIMIT_PER_MINUTE` / `LLM_RATE_WINDOW_SECONDS`); 429 when exceeded.
   Multi-worker deployments must swap for a shared store (Redis).
6. **Validate & sanitize uploads**; move images to object storage with signed URLs; scan types/size.
7. ✅ **Connector tokens encrypted at rest** (Fernet via `cryptography`; `CONNECTOR_ENCRYPTION_KEY`
   env, dev fallback derived from `JWT_SECRET`). Never returned by `GET /integrations`.
8. **Audit logging**: the event system already provides an audit substrate — add actor identity.
9. **Secrets hygiene**: keep everything in server-side env; never expose keys to the client.

---

## 26. Deployment Requirements — 100% free / open source

- **Runtime:** Python 3.11+ backend (uvicorn), Node 18+ for frontend build, MongoDB Community
  (or `mongomock` in-memory for dev/demo), local Ollama for AI (open weights).
- **Recommended stack:** `docker compose up --build` runs MongoDB + backend + frontend (nginx) on
  one machine; the frontend also deploys free to GitHub Pages via `.github/workflows/pages.yml`.
- **Routing invariant:** the ingress routes `/api/*` → backend:8001 and everything else → frontend.
  **All backend routes MUST stay under `/api`** or routing breaks.
- **Binding:** backend must bind `0.0.0.0:8001` (do not hard-code external URLs).
- **Env-driven config only:** never hard-code URLs/keys; read from env.
- **LLM:** defaults to local Ollama (`LLM_BASE_URL=http://localhost:11434/v1`,
  `LLM_MODEL=llama3.2-vision`) — no API key, no paid service. Never point at a paid endpoint by
  default.
- **Do NOT modify** `REACT_APP_BACKEND_URL` (frontend/.env) or `MONGO_URL` (backend/.env) in this
  managed environment.

---

## 27. Environment Variables Required

**Backend (`/app/backend/.env`):**
- `MONGO_URL` — MongoDB connection string (managed; do not change here).
- `DB_NAME` — database name.
- `CORS_ORIGINS` — comma-separated allowed origins (currently `*`).
- `LLM_MODEL` — open-weights model served by local Ollama (default `llama3.2-vision`; text-only hosts
  can use `llama3.2` and set `LLM_MODEL` accordingly).
- `LLM_BASE_URL` — OpenAI-compatible endpoint (default `http://localhost:11434/v1` = local Ollama;
  only override if you deliberately choose a remote provider).
- `LLM_API_KEY` — optional; local Ollama accepts any dummy key. Omitted/blank means local-only.

**Frontend (`/app/frontend/.env`):**
- `REACT_APP_BACKEND_URL` — public backend base (do not change; `/api` is appended in code).
- `WDS_SOCKET_PORT` — dev server websocket port.
- `ENABLE_HEALTH_CHECK` — health check flag.


---

## 28. Third-Party Services Required

- **Local Ollama (required for AI features; free & open source)** — `LLM_BASE_URL` defaults to
  `http://localhost:11434/v1` with `LLM_MODEL=llama3.2-vision`; run `ollama serve` + `ollama pull llama3.2-vision`.
  No API key, no account, no billing. Any other OpenAI-compatible endpoint is a deliberate override.
- **MongoDB Community (required)** — self-hosted (open source), or in-memory `mongomock` for dev/demo.
- **Optional connectors (off by default, simulated without credentials):** TradeMe API,
  Facebook Marketplace API, Gmail API (OAuth). Object storage (e.g., S3 — `boto3` already in
  requirements) for images remains a future option.

---

## 29. Local Development Instructions

> This project runs in a managed container with supervisor + preconfigured `.env`. To reproduce
> locally you would need your own MongoDB and an LLM key.

```bash
# Backend
cd /app/backend
pip install -r requirements.txt          # deps already installed in this env
# .env must contain MONGO_URL, DB_NAME, CORS_ORIGINS, LLM_API_KEY
# Do NOT run `python server.py` directly in this env — use supervisor:
sudo supervisorctl restart backend

# Frontend
cd /app/frontend
yarn install                              # NEVER use npm
sudo supervisorctl restart frontend

# Service status & logs
sudo supervisorctl status
tail -n 100 /var/log/supervisor/backend.*.log
tail -n 100 /var/log/supervisor/frontend.*.log

# Frontend compile sanity check (no npm):
cd /app/frontend && npx esbuild src/ --loader:.js=jsx --loader:.woff2=file --bundle --outfile=/dev/null

# Quick backend smoke test
curl ${REACT_APP_BACKEND_URL}/api/                      # health
curl -X POST ${REACT_APP_BACKEND_URL}/api/workspaces -H 'Content-Type: application/json' -d '{"name":"Dev"}'
```
**Rules:** use `yarn` (not npm); update `requirements.txt` only via `pip install ... && pip freeze`;
update `package.json` only via `yarn add`; never rewrite `.env` files.

---

## 30. Production Deployment Instructions (free / open source)

1. **Frontend → GitHub Pages:** push to `main`; `.github/workflows/pages.yml` builds `frontend/build`
   and deploys it. Optionally set `REACT_APP_BACKEND_URL` as a repository variable if the backend
   is hosted separately.
2. **Backend → self-host:** `docker compose up --build` (MongoDB + backend + nginx frontend) on any
   Linux machine you control. Or run `uvicorn server:app --host 0.0.0.0 --port 8001` under a
   process manager and reverse-proxy `/api/*` → backend, `/*` → static frontend.
3. **Environment:** set all env vars (see §27); set `CORS_ORIGINS` to your frontend origin(s).
   LLM vars already default to local Ollama — nothing paid to configure.
4. **Database:** self-hosted MongoDB Community (Docker volume) creates the recommended indexes
   (§24) automatically at startup.
5. **Before going live (must):** add authentication (§25), guard `/workspaces/{id}`, lock CORS,
   add rate limiting, and move images to object storage.
6. **Migrations:** `ensure_default_workspace()` runs on startup and stamps any legacy docs; keep
   this idempotent (or promote to an explicit migration step per §23).
7. **Observability:** ship the event log + application logs to your monitoring stack; alert on
   `AI_ERROR` rates and LLM latency.
> CI/CD runs free on GitHub Actions (`.github/workflows/`). HTTPS comes free with GitHub Pages;
> on a self-hosted backend, use a reverse proxy (e.g. Caddy — also open source) if you want HTTPS
> with a domain you already own. No paid platform or domain is required.

---

## 31. Testing Strategy

- **Isolation regression (critical):** `backend/tests/test_workspace_isolation.py` and
  `..._extended.py` create ≥2 workspaces and assert zero cross-tenant read/write leakage across all
  endpoints. Run these after ANY change touching data access. Latest result: 100% (27/27),
  `test_reports/iteration_4.json`.
- **AI POCs:** `backend/tests/test_core.py` (listing) and `test_core2.py` (vision + agent) validate the
  LLM contract independently of the API.
- **Manual API testing:** curl against `${REACT_APP_BACKEND_URL}/api` with different
  `X-Workspace-Id` headers.
- **Frontend compile check:** esbuild bundle (no npm) as a fast lint; then screenshots for visual QA.
- **Testing agent:** use for comprehensive backend/frontend regression after features; it writes
  `test_reports/iteration_{n}.json`. Always fix reported issues (even low priority) before shipping.
- **What's NOT auto-testable:** browser voice (Web Speech API) — verify manually in Chromium.
- **Recommended additions:** per-service unit tests after the refactor (§23); a seeded fixture
  workspace; contract tests asserting `_id` is never leaked and `workspace_id` always present.

---

## 32. Suggested Roadmap for the Next Six Months

**Month 1 — Foundation hardening & refactor**
- Split `server.py` into routers/services (§23); add DB indexes (§24); move test scripts to `tests/`.
- Add LLM retry/backoff + basic response caching.

**Month 2 — Authentication & authorization**
- Email/password + JWT (or Google Auth); users own workspaces; guard `/workspaces/{id}`;
  derive tenant from session; lock CORS; add rate limiting.

**Month 3 — Real TradeMe connector**
- OAuth + encrypted tokens; real listing draft creation behind the approval flow; real sync → pending suggestions; replace simulated market signals for
  TradeMe items. ✅ TradeMe connector shipped (Phase 14) — OAuth, encrypted tokens, approval-gated sync.

**Month 4 — Financials & object storage**
- Profit/fees/tax/margin reporting (use cost/tax_rate/currency); move images to object storage +
  thumbnails. ✅ Financials shipped (Phase 15) — `GET /api/financials` (potential P&L, category
  aggregation, currency-aware UI page); sales tracking shipped (Phase 15b) — realized vs
  potential P&L via `mark-sold`/`mark-unsold`; object storage shipped (Phase 16) — `image_blobs`
  + thumbnails + `GET /api/images/{id}`.

**Month 5 — Communications & workflow engine**
- Unified comms hub (real buyer messages/email via Gmail); workflow engine upgrade (Kanban/
  Calendar/Timeline + lifecycle states). ✅ Gmail adapter + inbox reply drafts (Phase 18);
  ✅ item lifecycle stages + Kanban/Timeline (Phase 19). Push/email notification channels pending.

**Month 6 — Scale & intelligence**
- Global search; scheduled background analysis + push notifications; workspace import; analytics on
  the event stream; multi-user roles/audit. ✅ Global search, CSV import, event analytics, and
  workspace members/roles (Phases 20–21); ✅ opt-in scheduler + in-app notifications (Phase 17).
  Remaining: push/email channels, live connector validation, per-sale COGS reconciliation.

---

## 33. Lessons Learned During Development

- **Retrofitting multi-tenancy is cheaper when the write path is centralized.** Because inserts and
  queries were funneled through consistent patterns, adding `workspace_id` + `get_wid` was tractable,
  and a lazy migration handled legacy data. Verifying with an automated isolation suite gave real
  confidence (100%).
- **A shared `call_llm` + `extract_json` paid off.** Five AI subsystems share one robust JSON parse
  and one client config; prompt changes are localized.
- **The Control Layer is a product feature, not overhead.** Making approval explicit (preview/
  reason/impact/confidence/risk) is what makes an "AI that changes your listings" trustworthy.
- **Simulated-but-honest beats fake.** Labeling market/lifecycle/inbox data as `(simulated)` keeps
  the product credible while the real integrations are pending.
- **A monolith is fine for velocity but has a shelf life.** ~1000 lines in one file accelerated the
  MVP; it now needs modularization before the next feature wave.
- **Budget discipline matters.** Prior sessions hit token limits mid-task; keeping `plan.md` and
  these docs current preserves context across handovers.

---

## 34. Major Design Decisions and Why

| Decision | Why |
|---|---|
| **Header-based tenant (`X-Workspace-Id`) + stateless backend** | Simple, cache-friendly, and forward-compatible with JWT-carried claims; no session store needed for MVP. |
| **Silent fallback to default workspace on missing/invalid header** | UX-safe with no auth (never hard-errors the UI); flagged to become strict once auth exists. |
| **UUID string ids, never ObjectId; always exclude `_id`** | Portability, no vendor lock-in, clean JSON, no accidental leakage of Mongo internals. |
| **Single shared LLM helper with strict-JSON prompts** | Consistency, one place to change model/parse behavior, resilient parsing. |
| **Approval-gated Control Layer** | Trust + safety: the AI never acts autonomously; every mutation is auditable. |
| **Per-workspace AI memory injected into all prompts** | Each business gets tailored AI behavior; isolation of "AI personality" per tenant. |
| **Simulated connectors/market signals with clear labeling** | Ship the full UX/architecture now; wire real APIs later without UI churn. |
| **Dark industrial design tokens + runtime re-skin per workspace** | Strong brand identity + white-label capability per business. |
| **Defer auth, but include auth libs and design for it** | Focus on core value first; avoid a painful refactor later by keeping tenant/user separable. |
| **TanStack Query + global invalidation on switch** | Guarantees UI reflects the active tenant with minimal bespoke state code. |
| **OpenAI-compatible LLM (openai SDK) → local Ollama** | One endpoint for text + vision; local, open weights, no API key, no per-token cost. |

---

## 35. Recommendations for Future Developers

1. **Treat workspace isolation as sacred.** Any new collection/endpoint MUST take `wid =
   Depends(get_wid)` and filter/insert `workspace_id`. Run the isolation suite before merging.
2. **Never break the `/api` prefix** or the `X-Workspace-Id` interceptor — both are load-bearing.
3. **Keep the Control Layer intact.** New AI capabilities that change data must route through
   suggestions + approval, not auto-execute.
4. **Use the shared helpers** (`call_llm`, `extract_json`, `log_event`, `build_ai_memory`) rather
   than re-implementing; extend them if needed.
5. **Add a `data-testid`** to every interactive/informative element; keep names role-based.
6. **Respect env rules:** `yarn` only; `pip freeze` to update requirements; never rewrite `.env`;
   never hard-code URLs/keys.
7. **The backend refactor (§23) is done** — keep new code in `routes/`/`services/` and run the
   local mongomock suites (`cd /app/backend && pytest`) plus the isolation suites before merging.
8. **Prioritize auth (§25) before any real multi-user/production exposure.**
9. **Keep `plan.md`, this handover, and the Development Diary current** — they are the memory of the
   project across sessions/teams.
10. ✅ **TradeMe connector implemented** behind the existing connect/sync endpoints
    (`services/integrations/trademe.py`): OAuth 1.0a (enabled when `TRADEME_CONSUMER_KEY/SECRET`
    are set), encrypted tokens, live sync producing pending (approval-gated) suggestions — never
    auto-post. Without credentials the legacy simulated toggle is preserved.

---

_End of handover. See `/app/PROJECT_STATE.md` for a fast continuation checklist and
`/app/docs/Listrix_Development_Diary.md` for the decision log and roadmap._
