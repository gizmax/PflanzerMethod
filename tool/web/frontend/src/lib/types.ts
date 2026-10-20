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
  /** počet feedbacků k variantě (API hubu) */
  feedback_count?: number;
  /** už jsem k variantě feedback odeslal(a)? */
  my_feedback?: boolean;
};

export type Feedback = {
  id: number;
  variant_id: number;
  role_id: number | null;
  severity: "critical" | "high" | "medium" | "low";
  department: string;
  category: string;
  score?: number | null;
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
  /** klíč kroku cesty -> jméno zástupce (starší DB: prázdné) */
  path_owners?: Record<string, string | null>;
  decider_name?: string | null;
  /** jméno PdM (zástupce kroku Produkt), pokud je to člověk */
  pm_name?: string | null;
  /** krok s AI náhradou -> člověk, který AI draft skutečně podepíše (ne vždy PdM) */
  confirmers?: Record<string, string>;
  /** kroky s AI náhradou, u kterých tým určil podepisujícího (ai_signers z Kickoffu) */
  ai_signers?: Record<string, string>;
  /** rozhodnutí z Rozhodnutí (Go/Iterate/Kill): vítěz a důvod */
  decision?: { decision: string; winner: string | null; rationale: string | null;
    decider: string | null; below_commitment?: number | null } | null;
  core?: string[];
  shortlist?: string[];
  async_deadline?: string | null;
  /** po Iterate: varianty druhého kola (prázdné = všechny) */
  variants_in_play?: string[];
  /** po Iterate: varianty, které vypadly (jen informace) */
  variants_dropped?: string[];
  /** přihlášení k náhledu; heslo je null, pokud ho hub nesmí ukázat */
  preview_login?: { user: string; password: string | null } | null;
  /** zabitý projekt: důvod a poučení */
  kill?: { reason: string | null; lessons: { text: string; by: string | null }[] } | null;
  risk_profile?: "throwaway" | "pilot" | "production";
};

export type MissingInfo = {
  collecting: boolean;
  missing: { name: string; steps: string[]; labels: string[] }[];
  text: string | null;
};

export type SignWindow = {
  window: string;
  label: string;
  state: string;
  signer: string | null;
  command: string;
};

export type VoteChoice = "go" | "iterate" | "kill";
export type VoteOut = { voter: string; choice: VoteChoice; winner: string | null; comment: string };

export type VotesState = {
  enabled: boolean;
  revealed: boolean;
  is_decider: boolean;
  decider: string | null;
  can_vote: boolean;
  can_reveal: boolean;
  voters: { name: string; voted: boolean }[];
  decider_voted: boolean;
  mine: VoteOut | null;
  votes: VoteOut[];
  tally: Record<VoteChoice, number> | null;
  command: string | null;
};
