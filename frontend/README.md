# Lanelines — frontend

React + TypeScript + Vite trading UI for the backend in `../backend`. See the
root [README](../README.md) for full setup (Postgres, backend, invite codes).

```
npm install
copy .env.example .env
npm run dev
```

## Structure

- `src/api/` — typed REST client (`client.ts`), hand-written types matching the
  backend's Pydantic schemas (`types.ts`), and the WebSocket subscription hook
  (`ws.ts`).
- `src/auth/` — `AuthContext`, session persisted in `localStorage`.
- `src/pages/` — one component per route.
- `src/components/` — shared UI: nav shell, order book, order ticket, auth guard.

Live updates (order book, trades, balance, ticker) come from a single `/ws`
connection per session; `useLiveChannels` in `src/api/ws.ts` subscribes to
whatever channels a page needs and is auto-subscribed to the caller's own
private `user:{id}` channel by the server.

## Checks

```
npx tsc -b
npm run lint
npm run build
```
