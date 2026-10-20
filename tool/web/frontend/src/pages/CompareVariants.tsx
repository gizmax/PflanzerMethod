import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../lib/api";
import type { Variant } from "../lib/types";
import { ErrorScreen, Loading, StateScreen } from "../components/StateScreen";
import { Md } from "../lib/text";
import { PreviewLogin } from "../components/PreviewLogin";
import type { ProjectDetail } from "../lib/types";
import { useIsDesktop, usePageTitle } from "../lib/hooks";

export default function CompareVariants() {
  const { slug } = useParams<{ slug: string }>();
  const [variants, setVariants] = useState<Variant[] | null>(null);
  const [shortlist, setShortlist] = useState<string[]>([]);
  const [title, setTitle] = useState("");
  const [decided, setDecided] = useState(false);
  const [detail, setDetail] = useState<ProjectDetail | null>(null);
  const [error, setError] = useState<unknown>(null);
  const desktop = useIsDesktop();
  usePageTitle("Varianty");

  useEffect(() => {
    if (!slug) return;
    Promise.all([api.getProject(slug), api.listVariants(slug)])
      .then(([d, vs]) => {
        setDetail(d);
        setTitle(d.project.name);
        setDecided(["session_2", "handoff", "killed"].includes(d.project.status));
        setShortlist(d.shortlist ?? []);
        setVariants(vs);
      })
      .catch(setError);
  }, [slug]);

  const back = `/${slug}`;
  if (error) return <ErrorScreen error={error} backTo={back} backLabel="Zpět na projekt" />;
  if (!variants) return <Loading />;
  if (variants.length === 0) {
    return (
      <StateScreen title="Varianty zatím nejsou" backTo={back} backLabel="Zpět na projekt">
        <p>Tým je ještě nepublikoval. Zkuste to později, nebo napište facilitátorovi.</p>
      </StateScreen>
    );
  }

  const killed = detail?.project.status === "killed";
  const won = detail?.project.status === "handoff" && detail.decision?.decision === "go"
    ? detail.decision.winner : null;
    // Náhled za Basic auth: iframe by skončil jako šedý box s 401 (stav jde z jiné domény nezjistit).
  const protectedPreview = !!detail?.preview_login;
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <Link to={back} className="inline-flex min-h-[44px] items-center text-accent underline">← {title || "Zpět na projekt"}</Link>
        <h1>Varianty k posouzení</h1>
        <p className="pf-help">
          Každou variantu otevřete, vyzkoušejte hlavní tok a napište, co vás zastaví.
        </p>
        {detail && <PreviewLogin detail={detail} />}
        {won && (
          <div className="rounded-md border border-accent p-3 text-sm space-y-1">
            <p><strong>Rozhodnutí padlo: vítězí varianta {won}.</strong></p>
            {detail?.decision?.rationale && <p><Md text={detail.decision.rationale} /></p>}
            <p>Další krok: Ship a PR (řeší tým). Feedback se píše už jen jako připomínka k vítězi.</p>
          </div>
        )}
        {killed && (
          <div className="rounded-md border border-sev-critical p-3 text-sm space-y-1">
            <p><strong>Projekt byl ukončen, feedback se už nesbírá.</strong>
              {detail?.kill?.reason ? <> Důvod: <Md text={detail.kill.reason} /></> : null}</p>
            {(detail?.kill?.lessons ?? []).map((l, i) => <p key={i}>Poučení: {l.text}</p>)}
          </div>
        )}
      </div>

      <ul className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {variants.map((v) => {
          const isWinner = !!won && v.name === won;
          const lost = !!won && v.name !== won;
          const short = decided && !won && shortlist.includes(v.name);
          const hasPreview = !!v.prototype_url;
          return (
            <li key={v.id}>
              <article className={`pf-card flex h-full flex-col gap-3 ${short ? "border-2 border-accent" : ""}`}
                aria-labelledby={`v-${v.id}`}>
                <div className="flex flex-wrap items-center gap-2">
                  <h2 id={`v-${v.id}`}>Varianta {v.name}</h2>
                  {short && decided && <span className="pf-pill">V užším výběru</span>}
                  {isWinner && <span className="pf-pill">Vítěz</span>}
                  {lost && <span className="pf-pill">Nebyla vybrána</span>}
                </div>
                <p className="text-sm text-muted">Varianta k rozhodnutí — není hotový produkt.</p>
                {v.description_md && <p className="text-sm"><Md text={v.description_md} /></p>}

                {desktop && hasPreview && protectedPreview && (
                  <div className="flex aspect-video flex-col items-center justify-center gap-3 rounded border border-line bg-soft p-4 text-center">
                    <p className="text-sm">Náhled je za heslem — klikněte na Otevřít náhled.</p>
                    <a href={v.prototype_url} target="_blank" rel="noopener noreferrer"
                      className="pf-button-secondary">
                      Otevřít náhled<span className="sr-only"> varianty {v.name} v novém okně</span>
                    </a>
                  </div>
                )}
                {desktop && hasPreview && !protectedPreview && (
                  <div>
                    <div className="aspect-video overflow-hidden rounded border border-line bg-soft">
                      <iframe src={v.prototype_url} title={`Náhled varianty ${v.name}`} className="h-full w-full"
                        sandbox="allow-scripts allow-same-origin allow-forms" loading="lazy" />
                    </div>
                    <p className="mt-1 text-sm text-muted">
                      Náhled nejde vložit? <a className="underline text-accent" href={v.prototype_url}
                        target="_blank" rel="noopener noreferrer">Otevřete ho v novém okně</a>.
                    </p>
                  </div>
                )}
                {!hasPreview && <p className="rounded border border-dashed border-line p-3 text-sm text-muted">Náhled zatím není.</p>}

                <p className="text-sm" aria-live="polite">
                  {v.my_feedback
                    ? <strong className="text-sev-low">Váš feedback: odeslán ✓</strong>
                    : <span className="text-muted">Váš feedback: zatím neodeslán</span>}
                  <span className="text-muted"> · feedbacků celkem: {v.feedback_count ?? 0}</span>
                </p>

                <div className="mt-auto flex flex-col gap-2">
                  {!killed && !lost && (
                    <Link to={`/${slug}/feedback/${v.id}`} className="pf-button w-full">
                      {isWinner ? "Napsat připomínku k vítězi"
                        : v.my_feedback ? "Dát další feedback" : "Dát feedback"}
                    </Link>
                  )}
                  {hasPreview && !(desktop && protectedPreview) && (
                    <a href={v.prototype_url} target="_blank" rel="noopener noreferrer"
                      className="pf-button-secondary w-full">
                      Otevřít náhled<span className="sr-only"> varianty {v.name} v novém okně</span>
                    </a>
                  )}
                </div>

                <details className="text-sm text-muted">
                  <summary className="pf-summary !font-normal">Technické údaje</summary>
                  <p>Postaveno: {v.builder}</p>
                  {v.preference_score !== null && <p>Skóre preferencí: {v.preference_score.toFixed(2)}</p>}
                </details>
              </article>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
