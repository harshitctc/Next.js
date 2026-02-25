CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE assets (
    id BIGSERIAL PRIMARY KEY,
    ticker TEXT UNIQUE NOT NULL,
    asset_class TEXT NOT NULL,
    sector TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE documents (
    id BIGSERIAL PRIMARY KEY,
    source_type TEXT NOT NULL CHECK (source_type IN ('news', 'sec_filing', 'research')),
    source_uri TEXT,
    published_at TIMESTAMPTZ,
    raw_text TEXT NOT NULL,
    embedding vector(1536),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX documents_embedding_ivfflat_idx ON documents
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE TABLE sentiment_signals (
    id BIGSERIAL PRIMARY KEY,
    document_id BIGINT REFERENCES documents(id) ON DELETE CASCADE,
    ticker TEXT NOT NULL,
    sentiment_score DOUBLE PRECISION NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    model_version TEXT NOT NULL,
    rationale TEXT,
    generated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE portfolio_snapshots (
    id BIGSERIAL PRIMARY KEY,
    account_id TEXT NOT NULL,
    as_of TIMESTAMPTZ NOT NULL,
    objective TEXT,
    risk_budget DOUBLE PRECISION,
    tower_user_embedding vector(128),
    tower_asset_embedding vector(128),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE allocations (
    id BIGSERIAL PRIMARY KEY,
    snapshot_id BIGINT REFERENCES portfolio_snapshots(id) ON DELETE CASCADE,
    ticker TEXT NOT NULL,
    target_weight DOUBLE PRECISION NOT NULL,
    confidence DOUBLE PRECISION,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE risk_metrics (
    id BIGSERIAL PRIMARY KEY,
    account_id TEXT NOT NULL,
    as_of TIMESTAMPTZ NOT NULL,
    var_95 DOUBLE PRECISION NOT NULL,
    var_99 DOUBLE PRECISION NOT NULL,
    cvar_95 DOUBLE PRECISION,
    drift_score DOUBLE PRECISION,
    breach_flag BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE explanations (
    id BIGSERIAL PRIMARY KEY,
    decision_type TEXT NOT NULL CHECK (decision_type IN ('sentiment', 'allocation', 'risk')),
    decision_id TEXT NOT NULL,
    model_name TEXT NOT NULL,
    model_version TEXT NOT NULL,
    feature_attributions JSONB NOT NULL,
    shap_summary JSONB,
    explanation_text TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE decision_logs (
    id BIGSERIAL PRIMARY KEY,
    decision_type TEXT NOT NULL,
    decision_id TEXT NOT NULL,
    account_id TEXT,
    ticker TEXT,
    input_payload JSONB NOT NULL,
    output_payload JSONB NOT NULL,
    explanation_id BIGINT REFERENCES explanations(id),
    policy_result JSONB NOT NULL,
    approved_by TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX sentiment_signals_ticker_time_idx ON sentiment_signals (ticker, generated_at DESC);
CREATE INDEX risk_metrics_account_time_idx ON risk_metrics (account_id, as_of DESC);
CREATE INDEX decision_logs_type_time_idx ON decision_logs (decision_type, created_at DESC);
