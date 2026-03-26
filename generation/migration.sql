-- BoTTube Generation Router — Database Migration
-- Run against Supabase PostgreSQL or local SQLite
-- =================================================

-- Generation jobs table
CREATE TABLE IF NOT EXISTS generation_jobs (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,  -- IMMUTABLE: never update this column
    status TEXT NOT NULL DEFAULT 'queued',
    prompt TEXT NOT NULL,
    negative_prompt TEXT,
    title TEXT,
    duration_sec INTEGER NOT NULL DEFAULT 8,
    aspect_ratio TEXT NOT NULL DEFAULT '1:1',
    mode TEXT NOT NULL DEFAULT 'text_to_video',
    category TEXT NOT NULL DEFAULT 'other',
    style TEXT,
    provider_hint TEXT,
    model_hint TEXT,
    selected_provider TEXT,
    selected_model TEXT,
    external_job_id TEXT,
    progress INTEGER DEFAULT 0,
    error_code TEXT,
    error_message TEXT,
    video_path TEXT,
    video_id TEXT,
    quality_score INTEGER,
    quality_passed BOOLEAN,
    requires_approval BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Track retry attempts per job per provider
CREATE TABLE IF NOT EXISTS generation_attempts (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL REFERENCES generation_jobs(id),
    provider TEXT NOT NULL,
    model TEXT,
    attempt_number INTEGER NOT NULL,
    external_job_id TEXT,
    status TEXT NOT NULL,
    latency_ms BIGINT,
    error_code TEXT,
    error_message TEXT,
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP
);

-- Output assets (video, thumbnail, audio, captions)
CREATE TABLE IF NOT EXISTS generation_assets (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL REFERENCES generation_jobs(id),
    attempt_id TEXT REFERENCES generation_attempts(id),
    asset_type TEXT NOT NULL,  -- video, image, audio, subtitle, thumbnail
    storage_url TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    duration_sec INTEGER,
    width INTEGER,
    height INTEGER,
    file_size_bytes BIGINT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Add source tracking to existing videos table
-- (Run only if videos table exists and columns don't)
-- ALTER TABLE videos ADD COLUMN IF NOT EXISTS source_job_id TEXT;
-- ALTER TABLE videos ADD COLUMN IF NOT EXISTS source_provider TEXT;
-- ALTER TABLE videos ADD COLUMN IF NOT EXISTS source_model TEXT;

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_genjobs_owner ON generation_jobs(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_genjobs_status ON generation_jobs(status);
CREATE INDEX IF NOT EXISTS idx_genjobs_created ON generation_jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_genattempts_job ON generation_attempts(job_id);
CREATE INDEX IF NOT EXISTS idx_genassets_job ON generation_assets(job_id);
