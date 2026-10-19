const API_BASE = "/api";
async function request(path, init) {
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
    return r.json();
}
export const api = {
    listProjects: () => request("/projects"),
    getProject: (slug) => request(`/projects/${slug}`),
    listVariants: (slug) => request(`/projects/${slug}/variants`),
    createVariant: (slug, payload) => request(`/projects/${slug}/variants`, {
        method: "POST",
        body: JSON.stringify(payload),
    }),
    listFeedback: (slug) => request(`/feedback?project=${encodeURIComponent(slug)}`),
    submitFeedback: (payload) => request("/feedback", {
        method: "POST",
        body: JSON.stringify(payload),
    }),
};
