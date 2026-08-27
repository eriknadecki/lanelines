# Lanelines

Kalshi-style prediction market for college swimming — order-book trading with
virtual currency on markets like "Will Princeton beat Harvard?" or "Who wins
the NCAA Championship?", fed by manual live meet updates during the season.
Teams and meets are entered through the admin panel, so it covers any
program — not tied to a single conference.

See `backend/` for the FastAPI + matching engine service and `frontend/` for the
React + TypeScript trading UI.

## Backend setup

```
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -e ".[dev]"
copy .env.example .env          # adjust if needed

cd ..
docker compose up -d            # starts Postgres

cd backend
alembic upgrade head
uvicorn app.main:app --reload
```

Health check: `GET http://127.0.0.1:8000/health` · API docs: `http://127.0.0.1:8000/docs`

To get a starting admin account and an invite code for signing up friends:

```
cd backend
python scripts/create_admin.py you@example.com yourname yourpassword
```

## Frontend setup

Run this in a second terminal, alongside the backend:

```
cd frontend
npm install
copy .env.example .env          # points at the backend; defaults to http://127.0.0.1:8000
npm run dev
```

Open `http://localhost:5173`. Sign up with the invite code from `create_admin.py`
above (either paste it into the signup form, or visit
`http://localhost:5173/signup?code=YOUR_CODE`).

## Tests

```
cd backend
pytest -q
ruff check .
```

```
cd frontend
npx tsc -b
npm run lint
```
