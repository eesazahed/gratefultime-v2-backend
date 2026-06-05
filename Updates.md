# Updates

## 2026-06-05 — Health + commit endpoint

- `GET /api/v1/` and `GET /health` now include `commit` (`hash`, `description`, `time`).
- Added `GET /api/v1/commit` returning latest git commit info.

## 2026-06-05 — Supabase new API key names

- Renamed `SUPABASE_SERVICE_ROLE_KEY` → `SUPABASE_SECRET_KEY` (`sb_secret_...`).
- Added optional `SUPABASE_PUBLISHABLE_KEY` (`sb_publishable_...`) for reference.
- Legacy `SUPABASE_SERVICE_ROLE_KEY` / `SUPABASE_ANON_KEY` still accepted as fallbacks.

## 2026-06-05 — Full infrastructure rewrite

- Replaced Flask/Gunicorn with **FastAPI + Uvicorn**.
- New layout: `api/routes`, `api/services`, `api/db`, `api/core`.
- Removed templates, static assets, and entire legacy `app/` package.
- Added `Dockerfile`, updated `setup.sh`, OpenAPI docs at `/docs`.
- Supabase remains the database; API contracts unchanged for mobile.

## 2026-06-05 — Remove all v1 legacy code

- Deleted `/api/v1/entries/*`, `/api/v1/users/*`, `/api/v1/ai/monthlysummary` routes.
- Removed Fernet encryption (`ENCRYPTION_KEY`), `gratitude_entries` table, and v1 bundle id (`app.gratefultime`).
- Slimmed `users` schema to v2-only fields; backend is auth + summarize + quota only.

## 2026-06-05 — Migrate database layer to Supabase

- Replaced Flask-SQLAlchemy with `supabase-py` client (`app/db/` repositories).
- Added `supabase/schema.sql` for `users`, `gratitude_entries`, `ai_usage` tables.
- Config now uses `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` (removed `SQLALCHEMY_DATABASE_URI`).
- Removed `flask_sqlalchemy`, `psycopg2-binary`, and `app/models.py`.

## 2026-06-05 — Align with updated v2-data.md

- Restored `POST /api/v1/auth/applelogin` to existing behavior: required `user_timezone`, `{ token }` only response, auth blueprint rate-limit exempt.
- Removed `google_user_id` from `User` model and migration SQL (spec: do not add).
- Added optional `APPLE_AUDIENCE_V2` env var (default `app.gratefultime.v2`).
- Safe handling when `fullName` is omitted on Apple login.

## 2026-06-05 — v2 auth: Apple Sign-In only

- Removed `POST /api/v1/auth/googlelogin` and Google auth helpers.
- v2 clients use existing `POST /api/v1/auth/applelogin` with bundle id `app.gratefultime.v2`.
- Apple token verification accepts both `app.gratefultime` (v1) and `app.gratefultime.v2` (v2).
- `user_timezone` is now optional on Apple login (v2 stores unlock hour on device).
- Apple login rate limited to 10/min per IP; response includes `message: Login successful`.

## 2026-06-05 — v2 Phase 1 (MVP)

- Extended `User` model with `is_plus`, `plus_expires_at`.
- Added `AiUsage` model for free-tier AI quota (1 recap per calendar month).
- Added `GET /api/v1/me` — returns `user_id`, `email`, `is_plus`, `ai_previews_remaining`.
- Added `POST /api/v1/summarize` — client-sent entries, validation, quota enforcement, Gemini markdown recap.
- Rate limits: `summarize` 5/min and 30/day per user.
- Added `migrations/001_v2_phase1.sql` for existing Postgres deployments.
- Added optional `GET /health` alias for health check.
