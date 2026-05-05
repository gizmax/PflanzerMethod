import type {
  Feedback,
  Project,
  ProjectDetail,
  Variant,
} from "./types";

const API_BASE = "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      "X-User": "tom@gizmax.cz", // TODO Slice X: real SSO
      ...(init?.headers || {}),
    },
    ...init,
  });
  if (!r.ok) {
    const text = await r.text();
    throw new Error(`HTTP ${r.status}: ${text}`);
  }
  return r.json() as Promise<T>;
}

export const api = {
  listProjects: () => request<Project[]>("/projects"),
  getProject: (slug: string) => request<ProjectDetail>(`/projects/${slug}`),
  listVariants: (slug: string) =>
    request<Variant[]>(`/projects/${slug}/variants`),
  createVariant: (slug: string, payload: Omit<Variant, "id" | "session_id" | "created_at">) =>
    request<Variant>(`/projects/${slug}/variants`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listFeedback: (slug: string) =>
    request<Feedback[]>(`/feedback?project=${encodeURIComponent(slug)}`),
  submitFeedback: (
    payload: Omit<Feedback, "id" | "submitted_by" | "submitted_at">
  ) =>
    request<Feedback>("/feedback", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};
