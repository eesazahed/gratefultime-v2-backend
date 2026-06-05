-- GratefulTime v2 backend schema (Supabase Postgres)
-- Run in Supabase SQL Editor. Backend uses SUPABASE_SECRET_KEY (sb_secret_...).

CREATE TABLE IF NOT EXISTS users (
    user_id BIGSERIAL PRIMARY KEY,
    username TEXT,
    email TEXT UNIQUE,
    user_timezone TEXT NOT NULL DEFAULT 'America/New_York',
    apple_user_id TEXT UNIQUE,
    is_plus BOOLEAN NOT NULL DEFAULT FALSE,
    plus_expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ai_usage (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, year, month)
);

CREATE INDEX IF NOT EXISTS idx_ai_usage_user_year_month
    ON ai_usage (user_id, year, month);
