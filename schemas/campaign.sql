-- opacite campaign state (SQLite)
-- Events are append-only; current status = latest event per (case_slug, broker_id).

CREATE TABLE IF NOT EXISTS schema_version (
  version INTEGER NOT NULL UNIQUE
);
INSERT OR IGNORE INTO schema_version (version) VALUES (1);

CREATE TABLE IF NOT EXISTS broker_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  case_slug TEXT NOT NULL,
  broker_id TEXT NOT NULL,
  event TEXT NOT NULL CHECK (event IN (
    'PLANNED', 'APPROVED', 'SUBMITTED', 'AWAITING_REPLY',
    'VERIFIED_REMOVED', 'RE_LISTED', 'MANUAL_REQUIRED', 'FAILED'
  )),
  lane TEXT,
  ts TEXT NOT NULL,
  evidence_path TEXT,
  meta_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_events_case_broker
  ON broker_events (case_slug, broker_id, id DESC);

CREATE INDEX IF NOT EXISTS idx_events_case_ts
  ON broker_events (case_slug, ts);
