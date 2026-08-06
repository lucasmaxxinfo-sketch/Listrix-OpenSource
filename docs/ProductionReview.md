# Listrix — Production Review

_Last updated: consolidation phase_

Listrix is an AI-powered marketplace operations intelligence system for resale businesses,
built on the FARM stack (FastAPI + React + MongoDB) with a local open-source LLM via the
public `openai` SDK (text + vision) — Ollama by default, no API key, no paid service.

## 1. Architecture Overview

**Backend (`/app/backend/server.py`)** — single FastAPI service, all routes under `/api`.
- Collections: `items`, `listings`, `events`, `performance`, `suggestions`, `price_history`,
  `briefs`, `feedback`, `integrations`, `inbox`.
- AI helpers: `call_llm` (shared, supports optional image via `ImageContent`), `generate_listing_ai`,
  vision analyze, `analyze_one` (marketing agent), assistant, brief.
- All AI outputs are structured JSON parsed by a shared `extract_json` helper.

**Frontend (`/app/frontend/src`)**
- `lib/api.js` — axios client + endpoint functions (single source of truth for API calls).
- `lib/queries.js` — React Query hooks with shared cache invalidation.
- `lib/derive.js` — pure presentational helpers (condition score, confidence, value, formatting).
- `components/` — reusable UI (ItemCard, ActionCard, ControlActionDialog, EventTimeline,
  DailyBriefing, WidgetCarousel, PerformanceIntelligence, AIAssistant, StatCard, layout/*).
- `pages/` — Dashboard (Command Center), Items, ItemDetail, Workflows, AIManager, Market,
  Inbox, IntegrationHub, AIControl.

## 2. Feature Set (delivered & verified)

- **Items & Listings**: create items (name, description, condition, image, optional cost/category),
  AI listing generation (title, description, suggested price, hashtags).
- **Vision Intelligence**: image → item type/category/brand/condition/features + value estimate;
  auto-fills the creation workflow.
- **Marketing Intelligence Agent**: per-item performance (status, likelihood, reason, action) +
  ranked action suggestions with confidence, expected impact/outcome, risk level.
- **Control Layer**: every AI action requires explicit approval via `ControlActionDialog`
  (preview + explanation + expected impact + confidence + risk + confirm). Backend logs
  `USER_APPROVED_ACTION` / `ACTION_APPROVED`.
- **Action Queue** (AI Manager): approve / reject; approved actions mutate the listing
  (price, title, keywords, urgency, relist, generate); rejections feed the learning loop.
- **Closed Feedback Loop**: `feedback` collection + applied/dismissed suggestion history is fed
  back into the agent prompt so it adapts and avoids repeating rejected suggestions.
- **Market signals & lifecycle** (simulated, deterministic): demand/competition/saturation/trend +
  estimated views/engagement/conversion — fed into the agent.
- **Business Performance Intelligence**: best/worst/needs-attention items, next actions, revenue opp.
- **Command Center dashboard**: Daily AI Briefing, live auto-rotating widgets, performance
  intelligence, recent items, event stream.
- **Live AI Assistant**: floating panel, text + browser voice (Web Speech API STT/TTS),
  spoken-style answers + recommendation cards, approval-gated.
- **Smart Inbox**: alerts, opportunities, recommended actions, simulated buyer messages with
  priority + suggested action + related item.
- **Integration Hub**: structure-only connectors (TradeMe, Facebook Marketplace, Gmail,
  Pricing Signals, Competitor Listings) with connect/sync + event logging. No auto-posting.
- **Event system**: unified timeline, color-coded, 25+ event types.

## 3. Improvements Made During Consolidation

- Standardised API access through `lib/api.js` and React Query hooks (no scattered fetches).
- Single shared LLM helper and `extract_json` — no duplicated prompt/parse logic.
- Unified dark charcoal + industrial orange design tokens in `index.css`; consistent
  card/spacing/typography and shadow/glow utilities in Tailwind config.
- Consistent loading, empty and error states across pages.
- Legacy test data cleared; schema normalised to the current item model.

## 4. Known Limitations / Remaining Recommendations

- **External integrations are structure-only** (simulated). Real TradeMe/Facebook/Gmail OAuth +
  API calls are not implemented (per requirements) — the connector schema and approval/event
  flow are in place for future wiring.
- **Market signals & listing lifecycle are simulated** deterministically; replace with real
  marketplace data via the Integration Hub when available.
- **Sales data is not tracked** — "likelihood of sale" and briefings are inferred from listing
  quality/pricing/time-on-market, not real conversions.
- **Voice** relies on the browser's Web Speech API (best in Chromium); not testable by automated agents.
- **Auth**: the app currently has no authentication (single-operator assumption).

## 5. Technical Debt

- `analyze-all` runs LLM calls concurrently (capped at 12); large inventories may need batching/queueing.
- Images stored as base64 on documents — fine for MVP, but object storage is recommended at scale.
- No automated retry/backoff on LLM calls yet (errors are caught, logged as `AI_ERROR`, surfaced to UI).

## 6. Future Roadmap

1. Real connector OAuth + live sync (TradeMe first) behind the existing approval flow.
2. Real engagement/sales ingestion to replace simulated signals.
3. Scheduled background analysis + push notifications.
4. Multi-user auth, roles and audit trail.
5. LLM retry/backoff + response caching for cost/latency.
