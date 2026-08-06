# Listrix — Resale Business OS

A multi-tenant, AI **business operating system for resellers**. It turns inventory into AI-generated
marketplace listings, runs an approval-gated **AI Marketing Manager** that scores listings and
suggests changes, tracks fees/tax/profit, and manages workspaces with full data isolation.

**100% open source, zero-cost stack — no paid APIs, no paid hosting, no domains required.**

| Layer     | Technology                                        | License |
|-----------|---------------------------------------------------|---------|
| Frontend  | React 19 (CRACO) · Tailwind · dark-industrial UI   | MIT     |
| Backend   | FastAPI (Python 3.12)                             | MIT     |
| Database  | MongoDB Community (or in-memory `mongomock` for dev/demo) | SSPL (self-hosted) |
| AI        | [Ollama](https://github.com/ollama/ollama) — local, private, open weights (`llama3.2-vision` default) | MIT / open weights |
| Hosting   | GitHub Actions CI · GitHub Pages frontend · self-host backend via Docker Compose | free |

## Quick start

### Option A — Docker Compose (self-hosted, one machine)

```bash
# 1. Start a local open-source AI (on the host):
ollama serve
ollama pull llama3.2-vision

# 2. Run the whole stack (MongoDB + backend + frontend):
docker compose up --build
# Frontend: http://localhost   Backend: http://localhost:8000/api/
```

### Option B — local dev

```bash
# Backend (terminal 1)
cd backend
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
uvicorn server:app --reload --port 8000   # in-memory DB fallback; no Mongo needed for a demo

# Frontend (terminal 2)
cd frontend
yarn install
yarn start                                # http://localhost:3000
```

The app is fully functional without a model server; AI features return a clear error until Ollama
is running. Point `LLM_BASE_URL`/`LLM_MODEL` elsewhere only if you deliberately choose another
OpenAI-compatible endpoint.

## Tests & CI

- Backend: `cd backend && pytest` — 88 passing, 3 skipped (live-LLM POCs, opt-in via
  `LISTRIX_RUN_LIVE_LLM_TESTS=1`).
- CI runs backend tests + a production frontend build on every push (`.github/workflows/ci.yml`).
- The frontend deploys to **GitHub Pages** automatically on `main` (`.github/workflows/pages.yml`).

## Deployment (free)

1. Push this repo to GitHub; CI runs automatically.
2. Frontend → **GitHub Pages** (free): enable Pages in repo settings and use the `pages.yml` workflow.
3. Backend → **self-host anywhere** with `docker compose up --build` (home server, Raspberry Pi,
   old laptop, or any Linux box you control). No domain needed — access it by IP, or point a domain
   you already own at it.
4. Optionally set `REACT_APP_BACKEND_URL` as a repository variable for the Pages build.

## Documentation

- `docs/HANDOVER.md` — full technical handover
- `docs/BUILDER_BRIEF.md` — run/host/package instructions
- `docs/Listrix_Development_Diary.md` — living development log
- `PROJECT_STATE.md` — fast continuation guide · `plan.md` — phase history

## License

[MIT](LICENSE) — free to use, modify, and self-host.
