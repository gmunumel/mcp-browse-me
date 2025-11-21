-- Chat transcript storage table (stateful chatbot)
CREATE TABLE IF NOT EXISTS chat_threads (
    session_id UUID PRIMARY KEY,
    messages JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_threads_updated_at ON chat_threads (updated_at DESC);
