# Lanelines

Kalshi-style prediction market for college swimming: order-book trading with
virtual currency, live WebSocket updates, an admin panel for setting up
meets/markets, and friend-invite-based signup.

## Stack

- **Backend**: FastAPI + SQLAlchemy 2.0 (Mapped/mapped_column style) + Alembic
  + PostgreSQL (psycopg3 driver). A framework-free custom price-time-priority
  limit order book matching engine lives in `backend/engine/`.
- **Frontend**: React 19 + TypeScript + Vite, oxlint, react-router-dom.
- **Auth**: JWT access/refresh tokens, invite-gated signup, admin role gating.
  Tokens live in localStorage ("remember me") or sessionStorage; `apiFetch` in
  `frontend/src/api/client.ts` silently refreshes on a 401 before giving up.

## Critical constraint: single machine only

The matching engine's order books and the WebSocket connection manager live
in a single process's **memory** (`app/core/deps.py`). The Fly app must run
as exactly one machine — a second machine would silently split the order book
across two independent processes. `fly.toml` sets `min_machines_running = 0`
specifically to stop `fly deploy` from provisioning a second machine for
zero-downtime HA. If `fly deploy` ever creates a second machine, run
`fly scale count 1` (from `backend/`) to fix it. Always verify with
`flyctl machines list -a lanelines-api` after a deploy — expect exactly one row.

## Local dev setup

```
docker compose up -d                          # Postgres, from repo root

cd backend
python -m venv .venv && .venv/Scripts/activate
pip install -e ".[dev]"
cp .env.example .env                          # JWT_SECRET can be any random string for local dev
alembic upgrade head
uvicorn app.main:app --reload --port 8000

cd frontend
npm install
npm run dev                                   # http://localhost:5173, proxies to :8000 by default
```

Local admin account: `python backend/scripts/create_admin.py you@example.com yourname yourpassword`
(idempotent — safe to re-run to reset a password or promote an existing user).

## Tests & linting (run before every commit)

```
cd backend
ruff check .
pytest -q          # spins up/truncates a lanelines_test DB via conftest.py — needs Docker Postgres running

cd frontend
npx tsc --noEmit
npx oxlint
npm run build      # also worth doing before a deploy — catches build-time errors tsc alone misses
```

## Deployment

Two independent targets, both deployed manually (no CD pipeline) after CI
(`.github/workflows/backend-tests.yml`, backend only) passes on `master`.

**Backend** — Fly.io, app `lanelines-api`:
```
cd backend
flyctl deploy       # release_command runs `alembic upgrade head` automatically
```
Verify after every deploy: `curl https://lanelines-api.fly.dev/api/v1/venues`
and `flyctl machines list -a lanelines-api` (must show 1 machine).

**Frontend** — Cloudflare Pages, project `lanelines`:
```
cd frontend
VITE_API_BASE_URL=https://lanelines-api.fly.dev npm run build
npx wrangler pages deploy dist --project-name=lanelines
```
**`VITE_API_BASE_URL` is baked in at build time, not runtime.** Forgetting it
silently falls back to `http://127.0.0.1:8000` in the built bundle — the
deployed site will fail every API call with no visible error (this has
actually happened and cost a debugging round-trip; always grep the built JS
for `lanelines-api.fly.dev` before deploying to confirm). Needs
`CLOUDFLARE_API_TOKEN` in the environment (Pages edit permission) — not
currently stored anywhere in this repo or its CI, so whoever deploys sources
it manually each time.

Confirm the live site picked up a deploy: `curl -s https://lanelines.pages.dev/
| grep -oE 'assets/index-[^"]+\.(js|css)'` and compare the hash to the build
just produced.

## Alembic autogenerate gotchas

Autogenerate has repeatedly missed things in this project — always read the
generated migration before applying it:
- Doesn't detect Postgres CHECK constraint **text** changes (only presence/absence).
- Doesn't detect new values added to a Postgres native enum — needs a manual
  `ALTER TYPE ... ADD VALUE` wrapped in `op.get_bind().execute(...)` /
  autocommit block.
- Detects a column rename as `drop_column` + `add_column` rather than
  `alter_column(new_column_name=...)` — rewrite by hand if the column has
  real data, or if the old and new types differ (use `postgresql_using=...`
  for a type-changing rename).
- Dropping an enum-typed column leaves the Postgres enum *type* itself
  orphaned — drop it explicitly in the same migration
  (`sa.Enum(...).drop(op.get_bind(), checkfirst=True)`).
- Unique constraints get generated with `None` as the constraint name, which
  breaks `downgrade()`'s `drop_constraint(None, ...)` — name it explicitly
  (Postgres's own default convention is `<table>_<column>_key`).

## Conventions this project follows

- Service-layer functions raise typed exceptions from `app/services/errors.py`
  (`NotFoundError`, `DeletionBlockedError`, `AlreadyExistsError`, etc.);
  API routes map them to HTTP status codes via a local `_to_http_error` helper
  — never let a raw `IntegrityError` reach the client.
- Duplicate-name checks are proactive (`select(...).where(name == x)` before
  insert), not exception-driven — matches the existing `UserAlreadyExistsError`
  pattern in `auth_service.py`.
- Deletion endpoints are safety-checked against orphaning real trading/payout
  activity (see `market_service.delete_market_group`,
  `meet_service.delete_meet`, etc.) — read `order_cancellation.py` before
  adding a new one that touches orders/trades.
- Every new service function gets integration test coverage for both its
  success path and its specific failure/blocking conditions — see
  `backend/tests/integration/` for the pattern.
- Admin UI forms use a button-as-status-indicator pattern (see `SubmitButton`
  / `useSubmitStatus` in `AdminPage.tsx`): click → "Working..." → the button
  itself turns green/red with the result, then reverts. Required fields get a
  red asterisk and a red border on validation failure instead of native
  browser popups (`useValidation` in the same file).
- Frontend color scheme is blue (swimming theme) via CSS custom properties in
  `frontend/src/index.css` (`--accent`, `--bg-subtle`, etc.) — don't hardcode
  colors, and keep light/dark variants in sync.

## Playwright verification

There's no committed Playwright setup — when UI changes need visual
verification, install ad-hoc (`npm install --no-save playwright` in
`frontend/`), write a throwaway `.cjs` script, screenshot, then **always**
clean up (`npm uninstall playwright`, delete the script and screenshots)
before committing. Don't leave smoke-test artifacts in the tree.
