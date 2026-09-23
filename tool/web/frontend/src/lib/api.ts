import type {
  Feedback,
  Project,
  ProjectDetail,
  Variant,
} from "./types";

const API_BASE = "/api";

// Dev-mode identity (PFLANZER_HUB_AUTH_MODE=dev). Set in frontend/.env.local.
const DEV_USER: string = import.meta.env.VITE_PFLANZER_DEV_USER || "dev@local";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      // Dev mode only (PFLANZER_HUB_AUTH_MODE=dev). In OIDC mode nginx drops this
      // header and the identity comes from the SSO session (see README-auth.md).
      "X-User": DEV_USER,
      ...(init?.headers || {}),
    },
    ...init,
  });
  if (r.status === 401) {
    // No SSO identity (session expired or hub not behind oauth2-proxy).
    // Pages render thrown errors via their error state.
    throw new Error(
      "HTTP 401: nejste přihlášeni přes SSO — obnovte stránku (F5) pro nové přihlášení."
    );
  }
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
