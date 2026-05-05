// Mirror of tool/web/backend/models.py — keep in sync.

export type Project = {
  id: number;
  slug: string;
  name: string;
  charter_md: string | null;
  status: string;
  decider_name: string | null;
  sponsor_name: string | null;
  ai_act_tier: string | null;
  data_class: string | null;
  throwaway_or_evolve: string | null;
  capacity_profile: string | null;
  capacity_person_days: number | null;
  xyz_hypothesis: string | null;
  primary_lagging_metric: string | null;
  leading_metric: string | null;
  guardrail_metric: string | null;
  kill_criteria: string | null;
  created_at: string;
  updated_at: string;
};

export type Role = {
  id: number;
  project_id: number;
  catalog_idx: number;
  catalog_label: string;
  status: string;
  ai_proxy_mode: string;
  human_owner: string | null;
  rationale: string | null;
};

export type Triage = {
  id: number;
  project_id: number;
  track: string;
  status: string;
  artefact_md: string;
  signed_by: string | null;
};

export type Variant = {
  id: number;
  session_id: number;
  name: string;
  builder: string;
  prototype_url: string;
  description_md: string | null;
  preference_score: number | null;
  created_at: string;
};

export type Feedback = {
  id: number;
  variant_id: number;
  role_id: number | null;
  severity: "critical" | "high" | "medium" | "low";
  department: string;
  category: string;
  score: number;
  rationale: string;
  ai_act_dimension: string | null;
  wcag_level: "A" | "AA" | "AAA" | "N/A" | null;
  is_ai_only: boolean;
  submitted_by: string;
  submitted_at: string;
};

export type ProjectDetail = {
  project: Project;
  roles: Role[];
  triage: Triage[];
};
