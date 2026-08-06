# Listrix — Builder Brief (hand this to your developer)

> **Who this is for:** the developer or agency that will host the app and/or build the Android app.
> **What it is:** a complete, tested full-stack web application. This document tells you how to run,
> deploy, and package it — **entirely on free, open-source software**. Nothing here requires access
> to the original author beyond the questions at the end.

## 1. What Listrix is

A web app for people who resell items (eBay / Facebook Marketplace / TradeMe sellers). It turns
inventory into AI-generated marketplace listings, tracks fees/tax/profit, manages an action queue
where AI changes need approval, includes a comms inbox, a Kanban workflow board, financials
(realized vs potential P&L), notifications, and multi-workspace data isolation.

**Stack:** React 19 (CRACO) frontend · FastAPI (Python 3.12) backend · MongoDB (self-hosted
Community edition, or in-memory `mongomock` for demo). **AI runs on local Ollama — open weights,
private, zero cost, no API key.** No paid API, host, or domain is required anywhere.

## 2. Repository layout

```
backend/            FastAPI app (server.py = app factory; routes/, services/, models/, db/)
frontend/           React app (src/, public/ = PWA assets, capacitor.config.json for Android)
docs/               HANDOVER.md (full technical detail), BUILDER_BRIEF.md (this file)
test_reports/       automated test evidence (iteration_*.json)
plan.md             phase history and status
PROJECT_STATE.md    fast-continuation guide
.github/workflows/  CI (tests + build) and GitHub Pages deploy
docker-compose.yml  self-host the entire stack on one machine
```

## 3. Running locally (quick check)

Backend (terminal 1):
```bash
cd backend
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
export MONGO_URL=mongomock://localhost     # in-memory DB, no MongoDB needed for a demo
export DB_NAME=listrix
export CORS_ORIGINS="*"
export JWT_SECRET="local-dev-secret"
uvicorn server:app --reload --port 8000
```
Frontend (terminal 2):
```bash
cd frontend
yarn install
export REACT_APP_BACKEND_URL=http://localhost:8000
yarn start          # open http://localhost:3000
```
AI (terminal 3, optional but recommended — open source):
```bash
ollama serve                        # install from https://github.com/ollama/ollama
ollama pull llama3.2-vision
```
Sanity: `curl http://localhost:8000/api/` → `{"message":"Listrix API is running"}`.
Tests: `cd backend && . .venv/bin/activate && pytest` → 88 passed / 3 skipped (the 3 skips are
live-LLM POCs, opt-in via `LISTRIX_RUN_LIVE_LLM_TESTS=1`).

> Note: use **yarn** in the frontend (never npm — lockfile is yarn). The backend `.env` file is a
> scrubbed template; set the values via environment variables or by editing your own copy. The app
> is fully usable without Ollama running — only AI features show a "model not reachable" error.

## 4. Deployment — 100% free

1. **Push this repo to GitHub.** CI (`.github/workflows/ci.yml`) runs backend tests + a frontend
   production build on every push. GitHub Actions is free for public repos.
2. **Frontend — GitHub Pages (free).** Push to `main` and the `pages.yml` workflow builds
   `frontend/build` and deploys it to `https://<you>.github.io/<repo>/`. No domain or hosting bill.
   (Optional: point a domain you already own at it — not required.)
3. **Backend — self-host anywhere you already have a machine** (home server, Raspberry Pi, old
   laptop, any Linux box):
   ```bash
   docker compose up --build        # MongoDB + backend + frontend (nginx)
   ```
   Access it by IP — no domain needed. If you deploy the backend separately from GitHub Pages,
   set `REACT_APP_BACKEND_URL` as a **repository variable** on GitHub and re-run the Pages build.
4. **Database — MongoDB Community (open source),** bundled by `docker compose` as a container.
   No Atlas account, no cloud.

## 5. Android app (Option B — APK)

Two paths; most sellers are served by Path 1:

- **Path 1 — PWA (no Google Play needed):** the frontend already includes a PWA manifest
  and a service worker (`frontend/public/manifest.json`, `sw.js`). After deploying
  per §4, Android/iPhone users open the site and choose **“Add to Home screen” / “Install app”**.
  It launches full-screen like a native app. Zero extra work.
- **Path 2 — Real APK with Capacitor (if the owner wants a Play Store listing):**
  ```bash
  cd frontend
  yarn install
  yarn build
  npx cap add android
  npx cap sync android
  npx cap open android   # build the APK/AAB in Android Studio, or:
  cd android && ./gradlew assembleRelease
  ```
  `capacitor.config.json` is already provided (`appId: com.listrix.app`). The APK loads the hosted
  backend — it is a wrapper around the web app, so §4 hosting is still required (the backend cannot
  run inside the phone). Sign the release build with a keystore the owner controls.

## 6. AI (LLM) — local and open source by default

- **Default (recommended):** the backend points at **local Ollama** — `LLM_BASE_URL` defaults to
  `http://localhost:11434/v1`, `LLM_MODEL` defaults to `llama3.2-vision` (open weights, handles text
  and images). No API key, no account, no per-token billing, data never leaves the machine.
- `LLM_API_KEY` is optional (local servers accept any dummy key).
- The codebase talks to a standard **OpenAI-compatible** endpoint, so if the owner ever explicitly
  chooses a remote provider, only `LLM_BASE_URL`/`LLM_MODEL`/`LLM_API_KEY` need to change — but
  Listrix ships with local-only defaults so it never silently calls a paid API.
- In Docker Compose, Ollama runs on the host and the backend reaches it via
  `http://host.docker.internal:11434/v1` (override with the `LLM_BASE_URL` env var).

## 7. Marketplace connectors (Connection Wizard — no code needed)

- **The app has a built-in Connection Wizard** (Integration Hub → "Set up"). The owner pastes the
  credentials, clicks **Test connection**, then **Save & connect**. Credentials are encrypted per
  business at rest and never shown again.
- Connectors are **optional external marketplaces** (TradeMe, Facebook Marketplace, Gmail) — they
  are off by default, cost nothing to run, and are never required for the app to work. Without
  credentials they run in **simulated mode** so the UI stays fully demoable. The wizard labels each
  connector "live" or "simulated" so there's no confusion.
- Sync only creates **pending suggestions** that the user approves — nothing is ever auto-posted,
  auto-priced, or auto-sent.

## 8. Before you ship — checklist

- [ ] `pytest` green in `backend/` (88 passed, 3 skipped without a live LLM).
- [ ] Backend env vars set: `MONGO_URL`, `DB_NAME`, `CORS_ORIGINS`, `JWT_SECRET` (LLM vars already
      default to local Ollama — no key needed).
- [ ] Frontend `REACT_APP_BACKEND_URL` points at the deployed backend; `yarn build` succeeds.
- [ ] HTTPS enabled if you use a domain (required for PWA install + service worker; GitHub Pages
      provides HTTPS automatically).
- [ ] `AUTH_REQUIRED=true` for multi-user mode (default `false` = single-operator, no login).
- [ ] Production security: set `CONNECTOR_ENCRYPTION_KEY`, a strong `JWT_SECRET`, and enable the
      scheduler (`SCHEDULER_ENABLED=true`) for background analysis.

## 9. Questions the owner should answer before you start

1. Branding: final app name (currently **Listrix**) and colours (currently dark-industrial with
   orange `#FF7A1A`)?
2. Which marketplace(s) matter first (TradeMe / Facebook / eBay)?
3. Do they need a Google Play APK (Path 2) or is “install from browser” (Path 1) fine?
4. Where will the backend live — the same machine as the frontend (`docker compose`) or a separate
   machine/VPS they already pay for?
5. Do they want to use their own domain, or is the free GitHub Pages URL fine?
