-- ============================================================
-- Farming Assistant — Supabase Database Migration
-- ============================================================
-- Run this in the Supabase SQL Editor (Dashboard → SQL Editor)
-- This creates all 5 tables + Row-Level Security policies.
-- ============================================================

-- Enable UUID extension (usually already enabled in Supabase)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─── Table 1: Farm Profiles ────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS farm_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    farm_name TEXT,
    state TEXT,
    district TEXT,
    area_hectares FLOAT,
    soil_type TEXT,
    irrigation_type TEXT,
    crops JSONB DEFAULT '[]'::jsonb,
    latitude FLOAT,
    longitude FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_farm_profiles_user_id ON farm_profiles(user_id);

-- RLS: Users can only access their own farm profiles
ALTER TABLE farm_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own farm profiles"
    ON farm_profiles FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create own farm profiles"
    ON farm_profiles FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own farm profiles"
    ON farm_profiles FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own farm profiles"
    ON farm_profiles FOR DELETE
    USING (auth.uid() = user_id);


-- ─── Table 2: Chat Sessions ────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    thread_id TEXT UNIQUE NOT NULL,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_active_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS ix_chat_sessions_thread_id ON chat_sessions(thread_id);

-- RLS
ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own chat sessions"
    ON chat_sessions FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create own chat sessions"
    ON chat_sessions FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own chat sessions"
    ON chat_sessions FOR UPDATE
    USING (auth.uid() = user_id);


-- ─── Table 3: Chat Messages ────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'tool')),
    content TEXT NOT NULL,
    tool_calls JSONB,
    tool_results JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_chat_messages_session_id ON chat_messages(session_id);

-- RLS: Access through session ownership
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view messages in own sessions"
    ON chat_messages FOR SELECT
    USING (
        session_id IN (
            SELECT id FROM chat_sessions WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can create messages in own sessions"
    ON chat_messages FOR INSERT
    WITH CHECK (
        session_id IN (
            SELECT id FROM chat_sessions WHERE user_id = auth.uid()
        )
    );


-- ─── Table 4: Prediction Logs ──────────────────────────────────────────

CREATE TABLE IF NOT EXISTS prediction_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    service_type TEXT NOT NULL,
    request_data JSONB,
    response_data JSONB,
    latency_ms FLOAT,
    success BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_prediction_logs_service_type ON prediction_logs(service_type);
CREATE INDEX IF NOT EXISTS ix_prediction_logs_created_at ON prediction_logs(created_at);
CREATE INDEX IF NOT EXISTS ix_prediction_logs_user_id ON prediction_logs(user_id);

-- RLS
ALTER TABLE prediction_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own prediction logs"
    ON prediction_logs FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Service can insert prediction logs"
    ON prediction_logs FOR INSERT
    WITH CHECK (TRUE);  -- Server-side inserts via service_role key


-- ─── Table 5: Farmer Memories ──────────────────────────────────────────

CREATE TABLE IF NOT EXISTS farmer_memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    namespace TEXT NOT NULL,
    key TEXT NOT NULL,
    value JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_farmer_memories_user_ns ON farmer_memories(user_id, namespace);
CREATE UNIQUE INDEX IF NOT EXISTS ix_farmer_memories_user_ns_key ON farmer_memories(user_id, namespace, key);

-- RLS
ALTER TABLE farmer_memories ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own memories"
    ON farmer_memories FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create own memories"
    ON farmer_memories FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own memories"
    ON farmer_memories FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own memories"
    ON farmer_memories FOR DELETE
    USING (auth.uid() = user_id);


-- ─── Auto-update updated_at trigger ────────────────────────────────────

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_farm_profiles_updated_at
    BEFORE UPDATE ON farm_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER set_farmer_memories_updated_at
    BEFORE UPDATE ON farmer_memories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================
-- Done! All 5 tables created with Row-Level Security.
-- ============================================================
