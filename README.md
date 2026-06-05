# GratefulTime v2 Backend

FastAPI + Supabase API for the local-first GratefulTime iOS app.

## Stack

| Layer | Tech |
|-------|------|
| API | FastAPI + Uvicorn |
| Database | Supabase (Postgres) |
| Auth | Apple Sign-In → HS256 JWT |
| AI | Gemini 2.5 Flash |
| Rate limits | SlowAPI (per user_id or IP) |

## Project layout

```
api/
  routes/       # HTTP endpoints
  services/     # business logic (Gemini, quota)
  db/           # Supabase data access
  core/         # JWT, Apple verify, rate limiting
  config.py     # env settings
main.py         # Uvicorn entrypoint
supabase/
  schema.sql    # run once in Supabase SQL Editor
```

## Routes

| Method | Path | Auth |
|--------|------|------|
| GET | `/api/v1/` | No |
| GET | `/health` | No |
| POST | `/api/v1/auth/applelogin` | No |
| GET | `/api/v1/me` | Bearer JWT |
| POST | `/api/v1/summarize` | Bearer JWT |

Interactive docs: `/docs`

## Setup

```bash
cp .env.example .env
# fill in SECRET_KEY, GEMINI_API_KEY, SUPABASE_URL, SUPABASE_SECRET_KEY

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# run schema in Supabase dashboard first, then:
uvicorn main:app --reload --port 8000
```

Or: `./setup.sh 8000`

## Environment

| Variable | Purpose |
|----------|---------|
| `SECRET_KEY` | JWT signing |
| `GEMINI_API_KEY` | Google AI |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SECRET_KEY` | `sb_secret_...` from dashboard — backend only |
| `SUPABASE_PUBLISHABLE_KEY` | `sb_publishable_...` — optional, not used by this API |
| `REDIS_URL` | Optional — future distributed rate limits |
| `GRATEFULTIME_DEV_MODE` | `true` for Expo Go (`host.exp.Exponent` aud) |
| `APPLE_AUDIENCE_V2` | Default `app.gratefultime.v2` |

## Docker

```bash
docker build -t gratefultime-api .
docker run -p 8000:8000 --env-file .env gratefultime-api
```

## Deploy on Hack Club Nest (systemd + Caddy)

| | |
|-|-|
| SSH | `eesa.hackclub.app` |
| URL | `https://gratefultime-v2.eesa.hackclub.app` |
| Port | `33540` → `127.0.0.1` (Caddy reverse proxy) |

```bash
ssh eesa.hackclub.app
cd ~/gratefultime-v2-backend
./deploy/install.sh
# add deploy/Caddyfile.snippet to ~/Caddyfile
systemctl --user reload caddy
```

Full steps: `scripts/nest-deploy.md`

Mobile `BaseUrl`: `https://gratefultime-v2.eesa.hackclub.app`

## Docker (optional)

```bash
docker build -t gratefultime-api .
docker run -p 8000:8000 --env-file .env gratefultime-api
```
