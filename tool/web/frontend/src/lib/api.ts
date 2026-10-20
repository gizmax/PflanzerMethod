import { getIdentity } from "./identity";
import type {
  Feedback, MissingInfo, Project, ProjectDetail, SignWindow, Variant, VoteChoice, VotesState,
} from "./types";

const API_BASE = "/api";

/** Chyba API s HTTP kódem — stránky z ní skládají české chybové obrazovky. */
export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const who = getIdentity()?.name;
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  // Dev režim (localhost / sdílené heslo): identita = jméno vybrané na úvodu.
  // V OIDC režimu proxy hlavičku zahodí a identita jde z SSO.
  // Hlavička musí být ISO-8859-1 safe, proto kódujeme.
  if (who) headers["X-User"] = encodeURIComponent(who);
  const r = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { ...headers, ...((init?.headers as Record<string, string>) || {}) },
  });
  if (!r.ok) throw new ApiError(r.status, await r.text());
  return r.json() as Promise<T>;
}

export const api = {
  listProjects: () => request<Project[]>("/projects"),
  getProject: (slug: string) =>
    request<ProjectDetail>(`/projects/${encodeURIComponent(slug)}`),
  getMissing: (slug: string) =>
    request<MissingInfo>(`/projects/${encodeURIComponent(slug)}/missing`),
  getWindows: (slug: string) =>
    request<{ windows: SignWindow[] }>(`/projects/${encodeURIComponent(slug)}/windows`),
  getVotes: (slug: string) =>
    request<VotesState>(`/projects/${encodeURIComponent(slug)}/votes`),
  castVote: (slug: string, v: { choice: VoteChoice; winner: string | null; comment: string }) =>
    request<VotesState>(`/projects/${encodeURIComponent(slug)}/votes`,
      { method: "POST", body: JSON.stringify(v) }),
  revealVotes: (slug: string) =>
    request<VotesState>(`/projects/${encodeURIComponent(slug)}/votes/reveal`, { method: "POST" }),
  listVariants: (slug: string) =>
    request<Variant[]>(`/projects/${encodeURIComponent(slug)}/variants`),
  listFeedback: (slug: string) =>
    request<Feedback[]>(`/feedback?project=${encodeURIComponent(slug)}`),
  submitFeedback: (payload: {
    variant_id: number;
    role_id: number | null;
    severity: Feedback["severity"];
    department: string;
    category: string;
    rationale: string;
    ai_act_dimension: string | null;
    wcag_level: Feedback["wcag_level"];
    is_ai_only: boolean;
  }) =>
    request<Feedback>("/feedback", { method: "POST", body: JSON.stringify(payload) }),
};
