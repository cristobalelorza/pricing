-- Pricing: Initial schema for Supabase PostgreSQL
-- Run this in your Supabase SQL Editor (Dashboard > SQL Editor > New Query)

-- Users table (our own auth, not Supabase auth)
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    credits_remaining INTEGER NOT NULL DEFAULT 5,
    openrouter_key TEXT DEFAULT '',
    runs_today INTEGER NOT NULL DEFAULT 0,
    runs_today_date TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Businesses (shared across all users)
CREATE TABLE IF NOT EXISTS businesses (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    industry TEXT DEFAULT '',
    location TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Service templates (shared across all users)
CREATE TABLE IF NOT EXISTS services (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    default_constraints TEXT DEFAULT '',
    estimated_hours REAL,
    hourly_rate REAL,
    normal_delivery_days INTEGER,
    fast_delivery_days INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Pricing results (user-scoped)
CREATE TABLE IF NOT EXISTS results (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    business_id TEXT DEFAULT '',
    filename TEXT NOT NULL,
    deal_json JSONB NOT NULL,
    result_json JSONB NOT NULL,
    note TEXT DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Feedback / bug reports
CREATE TABLE IF NOT EXISTS feedback (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    user_email TEXT NOT NULL,
    page_url TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'suggestion',
    message TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_results_user ON results(user_id);
CREATE INDEX IF NOT EXISTS idx_results_business ON results(business_id);
CREATE INDEX IF NOT EXISTS idx_feedback_status ON feedback(status);

-- Default admin account (password: admin)
-- The bcrypt hash for "admin" -- you can change the password after first login
INSERT INTO users (id, email, password_hash, credits_remaining, created_at)
VALUES ('admin', 'admin', '$2b$12$LJ3L6.eBf8DqGOfLhHOyvOQpnRiVz0rN4L0F8x0JTtHY.4E0PqPKe', 9999, NOW())
ON CONFLICT (id) DO NOTHING;
