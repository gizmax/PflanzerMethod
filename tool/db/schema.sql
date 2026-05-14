-- Pflanzer tool — SQLite schema v0
-- Apply via: python3 tool/db/migrate.py
-- Source of truth for FastAPI SQLModel + tool/cli/*.py.

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- ==========================================================================
-- projects
-- ==========================================================================
CREATE TABLE IF NOT EXISTS projects (
  id INTEGER PRIMARY KEY,
  slug TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  charter_md TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  status TEXT NOT NULL DEFAULT 'draft'
    CHECK (status IN ('draft','charter','triage','session_1','session_2','handoff','killed')),
  decider_name TEXT,
  decider_mandate_from TEXT,
  cpo_escalation_contact TEXT,
  sponsor_name TEXT,
  ai_act_tier TEXT
    CHECK (ai_act_tier IN ('minimal','limited','high','unacceptable')),
  data_class TEXT
    CHECK (data_class IN ('L1','L2','L3','L4')),
  throwaway_or_evolve TEXT
    CHECK (throwaway_or_evolve IN ('throwaway','evolve')),
  capacity_profile TEXT
    CHECK (capacity_profile IN ('default','regulated','audit-grade')),
  capacity_person_days INTEGER,
  xyz_hypothesis TEXT,
  primary_lagging_metric TEXT,
  leading_metric TEXT,
  guardrail_metric TEXT,
  kill_criteria TEXT,
  reinforcement_t7 TEXT,
  reinforcement_t30 TEXT,
  reinforcement_t60 TEXT,
  reinforcement_t90 TEXT,
  reinforcement_budget_pd REAL
);

CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);

-- ==========================================================================
-- roles (per project — vybraná podmnožina z 18-position role catalogu)
-- ==========================================================================
CREATE TABLE IF NOT EXISTS roles (
  id INTEGER PRIMARY KEY,
  project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  catalog_idx INTEGER NOT NULL,         -- 1..18
  catalog_label TEXT NOT NULL,
  status TEXT NOT NULL
    CHECK (status IN ('mandatory','recommended','optional','excluded')),
  ai_proxy_mode TEXT NOT NULL
    CHECK (ai_proxy_mode IN ('mode_1','mode_2','mode_3')),
  human_owner TEXT,
  expert_agent_path TEXT,
  rationale TEXT,
  UNIQUE (project_id, catalog_idx)
);

CREATE INDEX IF NOT EXISTS idx_roles_project ON roles(project_id);

-- ==========================================================================
-- triage (per project — 4 paralelní async tracks: discovery, security, legal, platform)
-- ==========================================================================
CREATE TABLE IF NOT EXISTS triage (
  id INTEGER PRIMARY KEY,
  project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  track TEXT NOT NULL
    CHECK (track IN ('discovery','security','legal','platform')),
  status TEXT NOT NULL
    CHECK (status IN ('pending','ok','blocked','deferred')),
  artefact_md TEXT NOT NULL,
  signed_by TEXT,
  signed_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (project_id, track)
);

-- ==========================================================================
-- sessions (1 = generative, 2 = decisional, 3 = iterate)
-- ==========================================================================
CREATE TABLE IF NOT EXISTS sessions (
  id INTEGER PRIMARY KEY,
  project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  type INTEGER NOT NULL CHECK (type IN (1,2,3)),
  starts_at TIMESTAMP,
  ends_at TIMESTAMP,
  decision TEXT
    CHECK (decision IN ('go','iterate','kill','pending','skipped')),
  decision_atribuce TEXT,
  decision_ts TIMESTAMP,
  notes_md TEXT
);

CREATE INDEX IF NOT EXISTS idx_sessions_project ON sessions(project_id);

-- ==========================================================================
-- variants (1-3 mockupy per session 1)
-- ==========================================================================
CREATE TABLE IF NOT EXISTS variants (
  id INTEGER PRIMARY KEY,
  session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  name TEXT NOT NULL,                   -- A, B, C
  builder TEXT NOT NULL
    CHECK (builder IN ('v0','bolt','lovable','stitch','cursor','figma-make','manual')),
  prototype_url TEXT NOT NULL,
  description_md TEXT,
  preference_score REAL,                -- 0..1, AI-only deflated max 0.5
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_variants_session ON variants(session_id);

-- ==========================================================================
-- role_preferences (Session 1 — preference matrix per role × variant)
-- 4 dimenze: user_value, effort, risk, strategic_fit (0..1 normalized).
-- commitment_level 0–3 per role (0 = neúčastnit se mezi-session, 3 = co-creation).
-- ==========================================================================
CREATE TABLE IF NOT EXISTS role_preferences (
  id INTEGER PRIMARY KEY,
  variant_id INTEGER NOT NULL REFERENCES variants(id) ON DELETE CASCADE,
  role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
  user_value REAL CHECK (user_value BETWEEN 0 AND 1),
  effort REAL CHECK (effort BETWEEN 0 AND 1),
  risk REAL CHECK (risk BETWEEN 0 AND 1),
  strategic_fit REAL CHECK (strategic_fit BETWEEN 0 AND 1),
  commitment_level INTEGER CHECK (commitment_level BETWEEN 0 AND 3),
  rationale TEXT NOT NULL,
  is_ai_only INTEGER NOT NULL DEFAULT 0 CHECK (is_ai_only IN (0, 1)),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (variant_id, role_id)
);

CREATE INDEX IF NOT EXISTS idx_role_pref_variant ON role_preferences(variant_id);
CREATE INDEX IF NOT EXISTS idx_role_pref_role ON role_preferences(role_id);

-- ==========================================================================
-- feedback (scored per variant per role)
-- ==========================================================================
CREATE TABLE IF NOT EXISTS feedback (
  id INTEGER PRIMARY KEY,
  variant_id INTEGER NOT NULL REFERENCES variants(id) ON DELETE CASCADE,
  role_id INTEGER REFERENCES roles(id) ON DELETE SET NULL,
  severity TEXT NOT NULL
    CHECK (severity IN ('critical','high','medium','low')),
  department TEXT NOT NULL,
  category TEXT NOT NULL,
  score REAL NOT NULL CHECK (score BETWEEN 0 AND 1),
  rationale TEXT NOT NULL,              -- POVINNÉ
  ai_act_dimension TEXT,
  wcag_level TEXT
    CHECK (wcag_level IN ('A','AA','AAA','N/A')),
  is_ai_only BOOLEAN NOT NULL DEFAULT 0,
  submitted_by TEXT NOT NULL,
  submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_feedback_variant ON feedback(variant_id);

-- ==========================================================================
-- decisions (decision log per project)
-- ==========================================================================
CREATE TABLE IF NOT EXISTS decisions (
  id INTEGER PRIMARY KEY,
  project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  type TEXT NOT NULL
    CHECK (type IN ('charter','triage','preference','conflict','handoff','kill','escalation')),
  body_md TEXT NOT NULL,
  atribuce_user TEXT NOT NULL,
  atribuce_ts TIMESTAMP NOT NULL,
  sso_id TEXT
);

CREATE INDEX IF NOT EXISTS idx_decisions_project ON decisions(project_id);

-- ==========================================================================
-- audit_log (DORA 7-letá retence)
-- ==========================================================================
CREATE TABLE IF NOT EXISTS audit_log (
  id INTEGER PRIMARY KEY,
  ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  actor TEXT NOT NULL,
  action TEXT NOT NULL,
  target_type TEXT,
  target_id INTEGER,
  payload_json TEXT,
  retention_until DATE
);

CREATE INDEX IF NOT EXISTS idx_audit_ts ON audit_log(ts);
CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit_log(actor);

-- ==========================================================================
-- prompts (DORA 7-letá retence promptů — devil's advocate Útok 8)
-- ==========================================================================
CREATE TABLE IF NOT EXISTS prompts (
  id INTEGER PRIMARY KEY,
  ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
  role_id INTEGER REFERENCES roles(id) ON DELETE SET NULL,
  model TEXT NOT NULL,
  prompt_text TEXT NOT NULL,
  response_text TEXT NOT NULL,
  retention_until DATE NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_prompts_project ON prompts(project_id);
CREATE INDEX IF NOT EXISTS idx_prompts_ts ON prompts(ts);
