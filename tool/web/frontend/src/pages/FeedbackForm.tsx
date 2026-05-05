import { FormEvent, useEffect, useState } from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import type { Feedback, Role, Variant } from "../lib/types";

const SEVERITIES = ["critical", "high", "medium", "low"] as const;
const WCAG = ["N/A", "A", "AA", "AAA"] as const;

export default function FeedbackForm() {
  const { slug, variantId } = useParams<{ slug: string; variantId: string }>();
  const navigate = useNavigate();
  const [variant, setVariant] = useState<Variant | null>(null);
  const [roles, setRoles] = useState<Role[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Form state
  const [roleId, setRoleId] = useState<number | null>(null);
  const [severity, setSeverity] = useState<Feedback["severity"]>("medium");
  const [department, setDepartment] = useState("");
  const [category, setCategory] = useState("");
  const [score, setScore] = useState(0.7);
  const [rationale, setRationale] = useState("");
  const [aiActDim, setAiActDim] = useState("");
  const [wcagLevel, setWcagLevel] = useState<Feedback["wcag_level"]>("N/A");
  const [isAiOnly, setIsAiOnly] = useState(false);

  useEffect(() => {
    if (!slug || !variantId) return;
    Promise.all([api.listVariants(slug), api.getProject(slug)])
      .then(([vs, detail]) => {
        const v = vs.find((x) => x.id === Number(variantId));
        setVariant(v ?? null);
        setRoles(detail.roles);
      })
      .catch((e) => setError(String(e)));
  }, [slug, variantId]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!variant) return;
    if (!rationale.trim()) {
      setError("Rationale je povinné (per metodika v0.2.1).");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const role = roles.find((r) => r.id === roleId);
      const dept = role?.catalog_label || department || "unknown";

      await api.submitFeedback({
        variant_id: variant.id,
        role_id: roleId,
        severity,
        department: dept,
        category: category || "general",
        score,
        rationale,
        ai_act_dimension: aiActDim || null,
        wcag_level: wcagLevel,
        is_ai_only: isAiOnly,
      });
      setSuccess(true);
      setTimeout(() => navigate(`/${slug}/compare`), 1500);
    } catch (e) {
      setError(String(e));
    } finally {
      setSubmitting(false);
    }
  }

  if (!variant) return <div className="pf-card">Načítám…</div>;

  // Score deflation warning (devil's advocate Útok 6 — heuristic, not measurement)
  const deflatedScore = isAiOnly && score > 0.5 ? 0.5 : score;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1>Feedback — Varianta {variant.name}</h1>
        <Link to={`/${slug}/compare`} className="pf-button-secondary">← Zpět</Link>
      </div>

      <form onSubmit={onSubmit} className="pf-card space-y-4 max-w-2xl">
        <div>
          <label className="pf-label">Role (z role catalogu projektu)</label>
          <select
            className="pf-input"
            value={roleId ?? ""}
            onChange={(e) => setRoleId(e.target.value ? Number(e.target.value) : null)}
          >
            <option value="">— vyber roli —</option>
            {roles.map((r) => (
              <option key={r.id} value={r.id}>
                #{r.catalog_idx} {r.catalog_label} ({r.ai_proxy_mode})
              </option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="pf-label">Severity</label>
            <select
              className="pf-input"
              value={severity}
              onChange={(e) => setSeverity(e.target.value as Feedback["severity"])}
            >
              {SEVERITIES.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="pf-label">Kategorie</label>
            <input
              className="pf-input"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              placeholder="např. ux, tech, security, legal, a11y"
            />
          </div>
        </div>

        <div>
          <label className="pf-label">
            Score závaznosti: <strong>{deflatedScore.toFixed(2)}</strong>
            {isAiOnly && score > 0.5 && (
              <span className="text-severity-high text-xs ml-2">
                (deflated z {score.toFixed(2)} kvůli AI-only)
              </span>
            )}
          </label>
          <input
            type="range"
            min={0}
            max={1}
            step={0.05}
            value={score}
            onChange={(e) => setScore(Number(e.target.value))}
            className="w-full"
          />
        </div>

        <div>
          <label className="pf-label">
            Rationale <span className="text-severity-critical">*</span>
          </label>
          <textarea
            className="pf-input min-h-[100px]"
            value={rationale}
            onChange={(e) => setRationale(e.target.value)}
            placeholder="Proč tento score? (povinné — bez rationale se rozhodnutí stává politickým)"
            required
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="pf-label">AI Act dimension (volitelné)</label>
            <input
              className="pf-input"
              value={aiActDim}
              onChange={(e) => setAiActDim(e.target.value)}
              placeholder="např. transparency, human oversight"
            />
          </div>
          <div>
            <label className="pf-label">WCAG level (jen A11y feedback)</label>
            <select
              className="pf-input"
              value={wcagLevel ?? "N/A"}
              onChange={(e) => setWcagLevel(e.target.value as Feedback["wcag_level"])}
            >
              {WCAG.map((w) => (
                <option key={w} value={w}>{w}</option>
              ))}
            </select>
          </div>
        </div>

        <label className="inline-flex items-center gap-2">
          <input
            type="checkbox"
            checked={isAiOnly}
            onChange={(e) => setIsAiOnly(e.target.checked)}
            className="rounded"
          />
          <span className="text-sm">
            AI-only feedback (bez human review) — score deflated max 0.5 (heuristic)
          </span>
        </label>

        {error && (
          <div className="rounded border border-severity-critical/30 bg-severity-critical/10 p-3 text-sm text-severity-critical">
            {error}
          </div>
        )}
        {success && (
          <div className="rounded border border-severity-low/30 bg-severity-low/10 p-3 text-sm text-severity-low">
            Feedback uložen. Přesměrovávám…
          </div>
        )}

        <div className="flex gap-2">
          <button type="submit" className="pf-button" disabled={submitting}>
            {submitting ? "Odesílám…" : "Odeslat feedback"}
          </button>
          <Link to={`/${slug}/compare`} className="pf-button-secondary">Zrušit</Link>
        </div>
      </form>
    </div>
  );
}
