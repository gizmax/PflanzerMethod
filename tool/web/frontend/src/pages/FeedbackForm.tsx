import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../lib/api";
import type { Feedback, ProjectDetail, Variant } from "../lib/types";
import { ErrorScreen, Loading } from "../components/StateScreen";
import { IdentityPicker } from "../components/IdentityPicker";
import { SEVERITY } from "../lib/text";
import { vocative } from "../lib/identity";
import { useIdentity, usePageTitle } from "../lib/hooks";

const SEVERITIES = ["critical", "high", "medium", "low"] as const;
const WCAG = ["N/A", "A", "AA", "AAA"] as const;
const AREAS: [string, string][] = [
  ["general", "Obecné"], ["ux", "Použitelnost"], ["security", "Bezpečnost"],
  ["legal", "Právo a soukromí"], ["tech", "Technika"], ["a11y", "Přístupnost"],
];

export default function FeedbackForm() {
  const { slug, variantId } = useParams<{ slug: string; variantId: string }>();
  const navigate = useNavigate();
  const [identity, setIdentity] = useIdentity();
  const [detail, setDetail] = useState<ProjectDetail | null>(null);
  const [variants, setVariants] = useState<Variant[]>([]);
  const [loadError, setLoadError] = useState<unknown>(null);

  const [severity, setSeverity] = useState<Feedback["severity"] | "">("");
  const [rationale, setRationale] = useState("");
  const [roleId, setRoleId] = useState<number | null>(null);
  const [area, setArea] = useState("general");
  const [aiActDim, setAiActDim] = useState("");
  const [wcagLevel, setWcagLevel] = useState<Feedback["wcag_level"]>("N/A");
  const [isAiOnly, setIsAiOnly] = useState(false);

  const [errors, setErrors] = useState<{ severity?: string; rationale?: string }>({});
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const variant = variants.find((x) => x.id === Number(variantId)) ?? null;
  usePageTitle(variant ? `Feedback k variantě ${variant.name}` : "Feedback");

  useEffect(() => {
    if (!slug) return;
    Promise.all([api.getProject(slug), api.listVariants(slug)])
      .then(([d, vs]) => { setDetail(d); setVariants(vs); })
      .catch(setLoadError);
  }, [slug, identity?.name]);

  // přechod na další variantu = čistý formulář
  useEffect(() => {
    setSeverity(""); setRationale(""); setErrors({}); setSubmitError(null);
    setSubmitted(false); setSubmitting(false);
  }, [variantId]);

  const back = `/${slug}/compare`;
  if (loadError) return <ErrorScreen error={loadError} backTo={`/${slug}`} backLabel="Zpět na projekt" />;
  if (!detail) return <Loading />;
  if (!variant) {
    return <ErrorScreenMissing back={back} />;
  }
  if (!identity) {
    return (
      <div className="space-y-4">
        <h1>Feedback k variantě {variant.name}</h1>
        <IdentityPicker owners={detail.path_owners ?? {}} onPick={setIdentity} />
      </div>
    );
  }

  const idx = variants.findIndex((x) => x.id === variant.id);
  const next = variants.slice(idx + 1).find((x) => !x.my_feedback) ?? variants[idx + 1];

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (submitting || submitted || !variant || !identity) return;
    const errs: typeof errors = {};
    if (!severity) errs.severity = "Vyberte, jak závažné to je.";
    if (!rationale.trim()) errs.rationale = "Napište, co vás zastavilo a proč.";
    setErrors(errs);
    if (errs.severity || errs.rationale) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      const role = detail?.roles.find((r) => r.id === roleId);
      await api.submitFeedback({
        variant_id: variant.id,
        role_id: roleId,
        severity: severity as Feedback["severity"],
        department: role?.catalog_label || identity.step,
        category: area,
        rationale: rationale.trim(),
        ai_act_dimension: aiActDim.trim() || null,
        wcag_level: wcagLevel,
        is_ai_only: isAiOnly,
      });
      setSubmitted(true);
      setVariants((vs) => vs.map((x) => x.id === variant.id
        ? { ...x, my_feedback: true, feedback_count: (x.feedback_count ?? 0) + 1 } : x));
    } catch {
      setSubmitError("Feedback se nepodařilo uložit. Zkontrolujte připojení a zkuste to znovu — text jsme nesmazali.");
      setSubmitting(false);
    }
  }

  if (submitted) {
    return (
      <section className="pf-card max-w-2xl space-y-4" role="status" aria-labelledby="ok-h">
        <h1 id="ok-h">Díky, {vocative(identity.name)}. Feedback k {variant.name} uložen</h1>
        <p className="text-muted">Můžete dát další feedback k jiné variantě, nebo se vrátit na přehled.</p>
        <div className="flex flex-col gap-2 sm:flex-row">
          {next && next.id !== variant.id && (
            <button type="button" className="pf-button" onClick={() => navigate(`/${slug}/feedback/${next.id}`)}>
              Další varianta ({next.name})
            </button>
          )}
          <button type="button" className="pf-button-secondary" onClick={() => navigate(back)}>Zpět na přehled</button>
        </div>
      </section>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <Link to={back} className="inline-flex min-h-[44px] items-center text-accent underline">← Zpět na varianty</Link>
        <h1>Feedback k variantě {variant.name}</h1>
        <p className="mt-1 text-sm text-muted">
          Dáváte feedback jako: <strong className="text-ink">{identity.name} · {identity.step}</strong>{" "}
          <button type="button" className="min-h-[44px] px-1 underline text-accent" onClick={() => setIdentity(null)}>
            změnit
          </button>
        </p>
      </div>

      <form onSubmit={onSubmit} noValidate className="pf-card max-w-2xl space-y-5">
        <p className="rounded-md bg-soft p-3 text-sm" id="howto">
          <strong>Dobrý feedback:</strong> co jsem zkoušel → co se stalo → co jsem čekal → co navrhuji.
          Jeden feedback = jeden problém.
        </p>

        <fieldset aria-describedby={errors.severity ? "sev-err" : undefined}>
          <legend className="pf-label">Jak závažné to je?</legend>
          <div className="grid gap-2 sm:grid-cols-2">
            {SEVERITIES.map((s) => (
              <label key={s} htmlFor={`sev-${s}`}
                className="flex min-h-[44px] cursor-pointer items-start gap-3 rounded-md border border-line p-3 has-[:checked]:border-2 has-[:checked]:border-accent has-[:checked]:bg-soft has-[:focus-visible]:outline has-[:focus-visible]:outline-[3px] has-[:focus-visible]:outline-accent">
                <input id={`sev-${s}`} type="radio" name="severity" value={s} checked={severity === s}
                  onChange={() => setSeverity(s)} className="mt-1 h-5 w-5 shrink-0 accent-[rgb(var(--c-accent))]" />
                <span>
                  <span className={`block font-semibold text-sev-${s}`}>{SEVERITY[s].label}</span>
                  <span className="block text-sm text-muted">{SEVERITY[s].hint}</span>
                </span>
              </label>
            ))}
          </div>
          {errors.severity && <p id="sev-err" role="alert" className="pf-error">{errors.severity}</p>}
        </fieldset>

        <div>
          <label htmlFor="rationale" className="pf-label">Co vás zastavilo a proč</label>
          <textarea id="rationale" className="pf-input min-h-[140px]" value={rationale}
            onChange={(e) => setRationale(e.target.value)}
            aria-invalid={!!errors.rationale}
            aria-describedby={errors.rationale ? "rationale-err howto" : "howto"}
            placeholder="U varianty A se platí bez souhlasu s podmínkami → riziko GDPR → přidat zaškrtávátko" />
          {errors.rationale && <p id="rationale-err" role="alert" className="pf-error">{errors.rationale}</p>}
        </div>

        <details className="rounded-md border border-line p-3">
          <summary className="pf-summary">Pokročilé</summary>
          <div className="mt-3 space-y-4">
            <div>
              <label htmlFor="adv-role" className="pf-label">Role z katalogu projektu</label>
              <select id="adv-role" className="pf-input" value={roleId ?? ""}
                onChange={(e) => setRoleId(e.target.value ? Number(e.target.value) : null)}>
                <option value="">— podle vašeho kroku ({identity.step}) —</option>
                {detail.roles.map((r) => (
                  <option key={r.id} value={r.id}>#{r.catalog_idx} {r.catalog_label} ({r.ai_proxy_mode})</option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="adv-area" className="pf-label">Oblast</label>
              <select id="adv-area" className="pf-input" value={area} onChange={(e) => setArea(e.target.value)}>
                {AREAS.map(([k, l]) => <option key={k} value={k}>{l}</option>)}
              </select>
            </div>
            <div>
              <label htmlFor="adv-ai" className="pf-label">Dimenze AI Act (volitelné)</label>
              <input id="adv-ai" className="pf-input" value={aiActDim} onChange={(e) => setAiActDim(e.target.value)}
                placeholder="např. transparentnost, lidský dohled" />
            </div>
            <div>
              <label htmlFor="adv-wcag" className="pf-label">Úroveň WCAG (jen u přístupnosti)</label>
              <select id="adv-wcag" className="pf-input" value={wcagLevel ?? "N/A"}
                onChange={(e) => setWcagLevel(e.target.value as Feedback["wcag_level"])}>
                {WCAG.map((w) => <option key={w} value={w}>{w}</option>)}
              </select>
            </div>
            <label htmlFor="adv-aionly" className="flex min-h-[44px] items-center gap-3">
              <input id="adv-aionly" type="checkbox" checked={isAiOnly} onChange={(e) => setIsAiOnly(e.target.checked)}
                className="h-5 w-5 accent-[rgb(var(--c-accent))]" />
              <span className="text-sm">Feedback napsala jen AI, bez lidské kontroly</span>
            </label>
          </div>
        </details>

        {submitError && <p role="alert" className="rounded border border-sev-critical p-3 text-sm font-medium text-sev-critical">{submitError}</p>}

        <div className="flex flex-col gap-2 sm:flex-row">
          <button type="submit" className="pf-button w-full sm:w-auto" disabled={submitting || submitted}>
            {submitting ? "Odesílám…" : "Odeslat feedback"}
          </button>
          <Link to={back} className="pf-button-secondary w-full sm:w-auto">Zrušit</Link>
        </div>
      </form>
    </div>
  );
}

function ErrorScreenMissing({ back }: { back: string }) {
  return (
    <div className="pf-card max-w-xl space-y-3">
      <h1>Varianta nenalezena</h1>
      <p className="text-muted">Zkontrolujte odkaz, který jste dostali.</p>
      <Link to={back} className="pf-button-secondary">Zpět na varianty</Link>
    </div>
  );
}
