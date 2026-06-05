# GratefulTime v2 — Backend build instructions (`v2-data.md`)

**Read this entire file before writing code.**

This document tells you exactly how to extend the **existing** backend repo for **GratefulTime v2** (local-first iOS app). It is the single source of truth for API contracts, architecture, and what to build vs deprecate.

---

## 0. Executive summary (architecture decision)

### v1 (original app + backend)

- **All journal entries stored on the server** (Postgres, Fernet-encrypted).
- Backend enforced **one entry per day per user timezone** on `POST /api/v1/entries`.
- Auth: **Apple Sign-In** only.
- AI: `GET /api/v1/ai/monthlysummary` — server **loads entries from DB**, calls Gemini.

### v2 (current mobile app — `gratefultime-v2`)

- **All journal entries stored on the iPhone** (SQLite). No account required to journal.
- **One entry per local calendar day** enforced **only on device** — backend must **NOT** store or gate daily entries.
- Auth: **Apple Sign-In** (required to subscribe to Plus and call AI).
- Billing: **RevenueCat** on device (`entitlement: plus`, package: `monthly`).
- AI: app sends **that month’s entries in the request body**; backend calls Gemini and returns markdown. **Do not persist journal text** (default).

### What the backend is for in v2

| In scope | Out of scope (v2) |
|----------|-------------------|
| Apple auth → JWT (existing route) | Storing gratitude entries |
| `POST /api/v1/summarize` (client payload → Gemini) | Timezone once-per-day submit logic |
| Plus / AI quota enforcement | Entry CRUD (`/api/v1/entries/*`) for v2 clients |
| Rate limits (userId if authed, IP if not) | Fernet encryption of journal fields on server |
| RevenueCat webhook (Phase 2) | Google auth (not used) |
| `GET /api/v1/me` | Server-side streaks / calendar |

```
┌─────────────────────────────┐              ┌─────────────────────────────┐
│  gratefultime-v2 (Expo iOS) │              │  gratefultime-backend       │
│                             │              │  (Flask — extend, don’t       │
│  SQLite: entries, settings  │   Bearer JWT │   rewrite from scratch)      │
│  Local: 1/day, streaks      │ ───────────► │                             │
│  RevenueCat: purchase Plus  │              │  Postgres: users, quotas     │
│  Cache: monthly_summaries   │ ◄─────────── │  Redis: rate limits          │
└─────────────────────────────┘   summary    │  Gemini: summarize only      │
                                             └─────────────────────────────┘
```

---

## 1. Repos and URLs

| Repo | Purpose |
|------|---------|
| **Mobile** | `gratefultime-v2` — Expo SDK 54, TypeScript |
| **Backend** | [`gratefultime-backend`](https://github.com/eesazahed/gratefultime-backend) — Python Flask (already deployed) |

**Backend stack (existing):** Flask, SQLAlchemy, Postgres/SQLite, Redis + Flask-Limiter, PyJWT, Gemini via `requests`, Gunicorn.

**App `ApiConfig` today:**

```typescript
BaseUrl: "https://api.gratefultime.app"   // set to your deployed host
AppleLoginPath: "/api/v1/auth/applelogin" // EXISTING — reuse as-is
SummarizePath: "/api/v1/summarize"       // NEW for v2
UseLiveApi: false                         // flip true when summarize route live
```

**Known deploy host (Nest):** `gratefultime.eesa.hackclub.app` — align DNS/`BaseUrl` with whatever you expose in production.

**iOS bundle id (v2):** `app.gratefultime.v2`  
**v1 Apple audience (legacy):** `app.gratefultime`

**Important:** Backend `verify_apple_token` uses `APPLE_AUDIENCE` in production. For v2 builds you must **also accept** `app.gratefultime.v2` (or update `APPLE_AUDIENCE` to v2). Expo Go dev uses `host.exp.Exponent` when `GRATEFULTIME_DEV_MODE=true`.

---

## 2. EXACT instructions for backend work

### Phase 1 — MVP (build this first)

1. **Use existing Apple auth** — `POST /api/v1/auth/applelogin` already implemented. **Do not add Google auth.** v2 mobile calls this route after `expo-apple-authentication`.

2. **Add summarize route** — `POST /api/v1/summarize` with **client-sent JSON body**. Do **not** read entries from `gratitude_entries` for this route.

3. **Extend `User` model** — add `is_plus`, `plus_expires_at` (and `ai_usage` table). **`apple_user_id` already exists** — no new auth id column.

4. **Add usage tracking** — table or columns for AI quota: free = **1 summarize per calendar month**; Plus = unlimited (or high cap).

5. **Enforce auth on summarize** — **401** without valid JWT. No anonymous summarize.

6. **Rate limiting** — reuse existing `get_user_or_ip()` in `app/__init__.py`: JWT valid → limit by `user_id`; else IP. Summarize must require JWT so limits are per-user.

7. **Do not** add entry storage endpoints for v2.

8. **Return JSON shapes exactly** as specified in §4–§8 (field names matter).

### Phase 2 — Billing trust

9. **RevenueCat webhook** — `POST /webhooks/revenuecat` → set `users.is_plus` / `plus_expires_at`.

10. **`GET /api/v1/me`** — return `{ isPlus, email, ... }` from **server** state, not client.

### Phase 3 — Optional later

11. Cloud sync (`/api/v1/sync/*`) — **not in scope now**; v2 has export/import JSON only.

### Explicitly do NOT

- Do not require backend for daily journaling.
- Do not port v1 “already submitted today” logic to summarize.
- Do not store request journal bodies in Postgres (unless you add opt-in backup later).
- Do not create a new FastAPI repo unless explicitly asked — **extend Flask repo**.

---

## 3. Legacy routes (keep, do not use from v2)

These exist for **v1** and stay for backward compatibility:

| Method | Path | Notes |
|--------|------|-------|
| POST | `/api/v1/auth/applelogin` | **v2 + v1** — Apple → JWT `{ token }` |
| GET/POST/DELETE | `/api/v1/entries/*` | Server-stored encrypted entries |
| GET | `/api/v1/ai/monthlysummary` | Loads entries from DB → Gemini |
| GET/POST | `/api/v1/users/*` | Settings, delete account (v1) |

**v2 app must never call `/entries` or `/ai/monthlysummary`.**

---

## 4. New routes (v2 — implement exactly)

### 4.1 Health (existing pattern)

```
GET /api/v1/
→ 200 { "message": "server running", "dev_mode": boolean }
```

Optional: add `GET /health` alias. Exempt from strict limits (already exempt routes in `app/__init__.py`).

---

### 4.2 Apple auth (EXISTING — v2 uses this, do not add Google)

```
POST /api/v1/auth/applelogin
Content-Type: application/json
```

Implemented in `app/auth/routes.py`. v2 mobile calls this after `expo-apple-authentication`.

**Request body (exact keys from existing backend):**

```json
{
  "identityToken": "<Apple identity JWT>",
  "user": "<Apple user identifier string>",
  "email": "user@example.com",
  "fullName": {
    "givenName": "Eesa",
    "familyName": "Zahed"
  },
  "user_timezone": "America/New_York"
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `identityToken` | Yes | Verified via Apple JWKS (`verify_apple_token`) |
| `user` | Yes | Must match `sub` in identity token |
| `user_timezone` | Yes | IANA timezone; v2 sends device zone via `Intl` |
| `email` | First login only | Apple may hide email on repeat sign-ins; existing users OK |
| `fullName` | Optional | Only populated on first Apple authorization |

**Server steps (already implemented):**

1. Verify Apple identity token.
2. Match `user` to token `sub`.
3. Find or create `User` by `apple_user_id`.
4. Return JWT: `{ "token": "<HS256 JWT with user_id>" }`.

**Response 200:**

```json
{
  "token": "<JWT string>"
}
```

**Errors (existing):**

| Status | Body |
|--------|------|
| 400 | `{ "message": "Could not fetch user timezone" }` |
| 400 | `{ "message": "Missing Apple identity token or user ID" }` |
| 400 | `{ "message": "Email required on first Apple login" }` |
| 401 | `{ "message": "Invalid identity token" }` |

**v2 mobile:** stores `token` in SQLite (`api_auth_token`); sends `Authorization: Bearer` on summarize. RevenueCat `logIn(appleUserId)`.

**Backend config for v2 bundle:** ensure token `aud` accepts `app.gratefultime.v2` (see §1).

---

### 4.3 Current user

```
GET /api/v1/me
Authorization: Bearer <JWT>
```

**Response 200:**

```json
{
  "message": "User information retrieved successfully",
  "data": {
    "user_id": 123,
    "email": "user@example.com",
    "is_plus": false,
    "ai_previews_remaining": 1
  }
}
```

- `is_plus`: from DB (RevenueCat webhook) or false until Phase 2.
- `ai_previews_remaining`: `0` if free quota used this month; omit or `-1` for Plus unlimited.

Use same `@require_auth` decorator as existing routes (`app/helpers/utils.py`).

---

### 4.4 Summarize (core v2 AI route)

```
POST /api/v1/summarize
Authorization: Bearer <JWT>   ← REQUIRED
Content-Type: application/json
Rate limit: per user_id (via existing limiter key_func)
```

**Request body (exact PascalCase — matches mobile `SummarizeApi.ts`):**

```json
{
  "Year": 2026,
  "Month": 3,
  "Entries": [
    {
      "Gratitude1": "string",
      "Gratitude2": "string",
      "Gratitude3": "string",
      "UserPrompt": "string",
      "UserResponse": "string"
    }
  ]
}
```

Also accept **snake_case** aliases (`gratitude_1`, etc.) if you want backward compatibility with old Gemini prompt code — but **PascalCase is canonical for v2**.

**Validation (re-validate on server):**

| Field | Min | Max |
|-------|-----|-----|
| Each gratitude | 5 | 100 chars |
| UserPrompt | 5 | 200 chars |
| UserResponse | 5 | 200 chars |

| Rule | Action |
|------|--------|
| Missing/invalid JWT | **401** `{ "message": "Missing or invalid token" }` |
| `Entries` empty | **400** `{ "message": "No entries found for this month" }` |
| Free user, quota exhausted | **403** `{ "message": "Free plan includes 1 AI recap per month. Upgrade to Plus." }` |
| Rate limit | **429** `{ "message": "Rate limit exceeded", "error": "too_many_requests", "status_code": 429 }` |
| Gemini failure | **503** `{ "message": "Failed to contact AI service" }` |

**Quota logic (server — source of truth):**

```python
FREE_AI_PREVIEWS_PER_MONTH = 1   # match SubscriptionConfig in app
PLUS_ENTITLEMENT = True          # users.is_plus

if not user.is_plus:
    if usage_count_for(user_id, year, month) >= FREE_AI_PREVIEWS_PER_MONTH:
        return 403
# after successful Gemini response:
increment_usage(user_id, year, month)   # only for free users, or always for analytics
```

**Response 200:**

```json
{
  "summary": "# March recap\n\n...markdown...",
  "message": "Monthly summary generated"
}
```

Mobile reads **`summary`** (lowercase) and optional **`message`**. Empty summary with message = error UX in app.

**Gemini implementation:**

- Reuse existing pattern from `app/ai/routes.py` (`gemini-2.5-flash` or current model env).
- **API key only in env** (`GEMINI_API_KEY`).
- Prompt: warm second-person monthly recap; markdown; reuse safety/moderation ideas from existing `system_prompt` if useful.
- **Do not write entries to `gratitude_entries` table.**
- **Do not log full request bodies in production.**

**Suggested DB addition:**

```sql
CREATE TABLE ai_usage (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES user(user_id),
  year INTEGER NOT NULL,
  month INTEGER NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (user_id, year, month)   -- one free recap per month; Plus bypasses check
);
```

For Plus users: skip quota check or use separate higher limit.

---

### 4.5 RevenueCat webhook (Phase 2)

```
POST /webhooks/revenuecat
Authorization: Bearer <REVENUECAT_WEBHOOK_SECRET>
```

On `INITIAL_PURCHASE`, `RENEWAL`, `CANCELLATION`, `EXPIRATION`:

- Map `app_user_id` → `User.apple_user_id` (RevenueCat logged in with Apple user id on client).
- Set `users.is_plus = true/false`, `plus_expires_at`.

---

## 5. User model changes (SQLAlchemy)

**Existing (`app/models.py`):**

```python
class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128), nullable=True)
    email = db.Column(db.String(128), unique=True, nullable=True)
    user_timezone = db.Column(db.String(64), default="America/New_York")
    apple_user_id = db.Column(db.String(255), unique=True, nullable=True)
    preferred_unlock_time = db.Column(db.Integer, default=20)
    account_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), ...)
```

**Add for v2:**

```python
is_plus = db.Column(db.Boolean, default=False)
plus_expires_at = db.Column(db.DateTime(timezone=True), nullable=True)
```

`apple_user_id` already exists — **do not add google_user_id**.

---

## 6. Rate limiting (already implemented — use as-is)

From `app/__init__.py`:

```python
def get_user_or_ip():
    token = request.headers.get('Authorization', None)
    if token and token.startswith("Bearer "):
        token = token.split(" ")[1]
        try:
            user_id = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])['user_id']
            return user_id
        except:
            pass
    return get_remote_address()
```

**Required behavior for v2:**

| Route | Auth | Limit key |
|-------|------|-----------|
| `POST /auth/applelogin` | No | IP optional (auth_bp currently exempt) |
| `POST /summarize` | **Required** | `user_id` |
| `GET /me` | Required | `user_id` |
| `GET /api/v1/` | No | exempt |

Default global limit today: `10 per minute` — consider stricter per-route limits on summarize (e.g. `5 per minute`, `30 per day` for Plus).

---

## 7. Environment variables

**Existing (`.env.example` in backend repo):**

```bash
SECRET_KEY=
ENCRYPTION_KEY=          # still needed for legacy /entries routes
GEMINI_API_KEY=
GRATEFULTIME_DEV_MODE=false
REDIS_URL=               # optional local dev
SQLALCHEMY_DATABASE_URI= # optional local dev (defaults SQLite)
```

**Add for v2:**

```bash
REVENUECAT_WEBHOOK_SECRET=
# Optional: APPLE_AUDIENCE_V2=app.gratefultime.v2 if supporting multiple bundle ids
```

---

## 8. Mobile app contract (what v2 sends today / will send)

### Entry shape (local SQLite only — for your prompt context)

```typescript
type GratitudeEntry = {
  Id: number;
  Entry1: string;
  Entry2: string;
  Entry3: string;
  UserPrompt: string;
  UserPromptResponse: string;
  CreatedAt: string; // ISO UTC
};
```

### Summarize payload builder (`services/SummarizeApi.ts`)

Mobile builds:

```typescript
{
  Year: number,       // from first entry in month or now
  Month: number,      // 1-12
  Entries: [{
    Gratitude1: Entry.Entry1,
    Gratitude2: Entry.Entry2,
    Gratitude3: Entry.Entry3,
    UserPrompt: Entry.UserPrompt,
    UserResponse: Entry.UserPromptResponse,
  }]
}
```

### Summarize client behavior

- `UseLiveApi === false` → offline markdown preview (no network).
- `UseLiveApi === true` → `POST {BaseUrl}{SummarizePath}` with JSON body + `Authorization: Bearer` when signed in.
- **429** → show `"Rate limit exceeded. Please try again later."`
- Parses `summary` and `message` from JSON; also accepts FastAPI-style `detail` on errors.

### Auth (mobile — implemented)

1. User taps **Sign in with Apple** → `expo-apple-authentication`.
2. `POST {BaseUrl}/api/v1/auth/applelogin` with `identityToken`, `user`, `email`, `fullName`, `user_timezone`.
3. Store backend `{ token }` in SQLite (`api_auth_token`); Apple user id in `apple_user_*` settings keys.
4. Attach `Authorization: Bearer {token}` on summarize.
5. RevenueCat `logIn(appleUserId)` for Plus purchases.

### Plus (mobile)

```typescript
PlusEntitlementId: "plus"
PlusMonthlyPackageId: "monthly"
FreeAiPreviewsPerMonth: 1
```

Client gates UI; **server must enforce** on `/summarize` for production.

---

## 9. What stays on the phone only (backend must not duplicate)

| Concern | Where handled |
|---------|----------------|
| One entry per day | `EntryRepository` + local date key `YYYY-MM-DD` |
| Streaks | `ComputeStreakStats.ts` |
| Unlock hour | `SettingsRepository` / `AppSettingsContext` |
| Themes / prompts / widget | Client + RevenueCat |
| Monthly recap cache | SQLite `monthly_summaries` |
| Backup | `ExportImportService` JSON file |

---

## 10. Subscription tiers (reference)

| Tier | Price | Includes |
|------|--------|----------|
| **Free** | $0 | Daily entry, current streak, default theme, local backup, **1 AI recap/month** |
| **Plus** | ~$4.99/mo | Unlimited AI recaps, 3 premium themes, premium prompts, iOS widget, full Home stats |

**Backend enforces:** AI quota only (Phase 1). Themes/widget are client-only.

---

## 11. Security checklist

- [ ] Gemini key server-only
- [ ] Verify Apple identity token (`aud`, `iss`, expiry) — support v2 bundle id
- [ ] JWT via existing `SECRET_KEY` / HS256
- [ ] Summarize requires auth — no anonymous AI
- [ ] Rate limit auth endpoint by IP
- [ ] Do not persist journal text from summarize requests
- [ ] Do not log journal text in prod
- [ ] HTTPS in production
- [ ] RevenueCat webhook secret validation (Phase 2)

---

## 12. Mobile integration checklist (after deploy)

In `gratefultime-v2`:

1. Set `ApiConfig.BaseUrl` to deployed backend URL.
2. Set `ApiConfig.UseLiveApi = true`.
3. Apple login wired via `AuthContext` → `POST /api/v1/auth/applelogin`.
4. `SummarizeApi` sends `Authorization: Bearer` from stored token.
5. Optionally call `GET /api/v1/me` for server `is_plus`.
6. Handle 401 → re-auth; 403 → paywall; 429 → existing copy.

---

## 13. Key files in existing backend repo

| File | Purpose |
|------|---------|
| `app/__init__.py` | App factory, limiter, `get_user_or_ip` |
| `app/config.py` | Env config |
| `app/models.py` | User, GratitudeEntry |
| `app/helpers/utils.py` | JWT encode/decode, `@require_auth`, Apple verify |
| `app/auth/routes.py` | Apple login — **reuse for v2** |
| `app/ai/routes.py` | Legacy monthlysummary — **add POST summarize** |
| `app/entries/routes.py` | Legacy v1 only — **v2 does not call** |

---

## 14. Key files in mobile repo (`gratefultime-v2`)

| Path | Purpose |
|------|---------|
| `constants/ApiConfig.ts` | BaseUrl, AppleLoginPath, SummarizePath, UseLiveApi |
| `services/SummarizeApi.ts` | Payload + fetch with Bearer token |
| `context/AuthContext.tsx` | Apple Sign-In → backend JWT |
| `storage/SubscriptionRepository.ts` | apple_user_*, api_auth_token, plus flags |

---

## 15. EXACT Cursor prompt (paste in `gratefultime-backend` repo)

```
Read v2-data.md in full. GratefulTime v2: entries on iPhone only; backend for Apple auth (existing), summarize, Plus quotas.

Do NOT add Google auth.

Implement Phase 1 on existing Flask repo:
1. Add is_plus, plus_expires_at to User + ai_usage table for monthly quota.
2. GET /api/v1/me — JWT required.
3. POST /api/v1/summarize — JWT required, PascalCase body from client, Gemini, no entry persistence. Free: 1/month; Plus: unlimited.
4. Ensure APPLE_AUDIENCE accepts app.gratefultime.v2 for v2 iOS builds.
5. Keep POST /api/v1/auth/applelogin unchanged (v2 uses it).
6. Keep legacy /entries and GET /ai/monthlysummary for v1.

Match v2-data.md §4. Reuse Gemini prompts from app/ai/routes.py.
```

---

## 16. Quick test commands (after implement)

```bash
# Health
curl -s https://YOUR_HOST/api/v1/

# Summarize (requires JWT from Apple login first)
curl -s -X POST https://YOUR_HOST/api/v1/summarize \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer JWT_HERE" \
  -d '{
    "Year": 2026,
    "Month": 3,
    "Entries": [{
      "Gratitude1": "Good coffee",
      "Gratitude2": "A walk outside",
      "Gratitude3": "Time to reflect",
      "UserPrompt": "What made you smile?",
      "UserResponse": "Talking with a friend"
    }]
  }'
```

---

*Last updated for local-first v2 + existing `gratefultime-backend` Flask repo. Copy this file into the backend repo root before starting Cursor.*
