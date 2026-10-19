import { useEffect, useState, type ReactNode } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../lib/api";
import type { ProjectDetail, Variant } from "../lib/types";
import { ErrorScreen, Loading } from "../components/StateScreen";
import { IdentityPicker } from "../components/IdentityPicker";
import { Md, formatDate, ownerLabel, phaseLabel } from "../lib/text";
import { PATH_STEPS } from "../lib/identity";
import { buildTask, firstName, previewLoginText, splitHypothesis } from "../lib/task";
import { useIdentity, usePageTitle } from "../lib/hooks";

export default function ProjectPage() {
  const { slug } = useParams<{ slug: string }>();
  const [data, setData] = useState<ProjectDetail | null>(null);
  const [variants, setVariants] = useState<Variant[]>([]);
  const [error, setError] = useState<unknown>(null);
  const [identity, setIdentity] = useIdentity();

  usePageTitle(data?.project.name ?? "Projekt");

  useEffect(() => {
    if (!slug) return;
    api.getProject(slug).then(setData).catch(setError);
  }, [slug]);

  useEffect(() => {
    if (!slug) return;
    api.listVariants(slug).then(setVariants).catch(() => setVariants([]));
  }, [slug, identity?.name]);

  if (error) return <ErrorScreen error={error} />;
  if (!data) return <Loading />;

  const { project, roles, triage } = data;
  const owners = data.path_owners ?? {};
  const names = variants.map((v) => v.name);
  const range = names.length > 1 ? `${names[0]}–${names[names.length - 1]}` : names[0] ?? "A–C";
  const done = variants.filter((v) => v.my_feedback).length;
  const inAsync = project.status === "session_1";
  const task = buildTask(data, identity, range,
    data.async_deadline ? formatDate(data.async_deadline) : null, project.slug);
  const confirmer = firstName(data.pm_name);
  const killed = project.status === "killed";
  const login = previewLoginText(data);
  const hyp = project.xyz_hypothesis ? splitHypothesis(project.xyz_hypothesis, data.risk_profile) : null;

  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <h1>{project.name}</h1>
        <p className="pf-pill">{phaseLabel(project.status)}</p>
      </header>

      {!identity ? (
        <IdentityPicker owners={owners} onPick={setIdentity} />
      ) : (
        <p className="text-sm text-muted">
          Jste přihlášen(a) jako <strong className="text-ink">{identity.name} · {identity.step}</strong>{" "}
          <button type="button" className="underline text-accent min-h-[44px] px-1" onClick={() => setIdentity(null)}>
            změnit
          </button>
        </p>
      )}

      {killed && (
        <section className="pf-card border-sev-critical space-y-2" aria-labelledby="kill-h">
          <h2 id="kill-h">Projekt byl ukončen</h2>
          <p>Feedback se už nesbírá.{data.kill?.reason ? <> Důvod: <Md text={data.kill.reason} /></> : null}</p>
          {data.kill && data.kill.lessons.length > 0 ? (
            <div>
              <h3 className="mb-1">Poučení</h3>
              <ul className="list-disc pl-5 space-y-1">
                {data.kill.lessons.map((l, i) => <li key={i}>{l.text}{l.by ? <span className="text-muted"> — {l.by}</span> : null}</li>)}
              </ul>
            </div>
          ) : <p className="text-sm text-muted">Poučení zatím není zapsané.</p>}
        </section>
      )}
      {inAsync && (
        <section className="pf-card border-accent space-y-3" aria-labelledby="task-h">
          <h2 id="task-h">Vaše úloha</h2>
          {task.lead && <p>{task.lead}</p>}
          <ol className="list-decimal pl-5 space-y-1">
            {task.steps.map((t, i) => <li key={i}>{t}</li>)}
            {task.key !== "decider" && data.async_deadline && (
              <li>Do <strong>{formatDate(data.async_deadline)}</strong>.</li>
            )}
          </ol>
          {task.command && (
            <pre className="overflow-x-auto rounded-md bg-soft p-3 text-sm whitespace-pre-wrap break-words"><code>{task.command}</code></pre>
          )}
          {variants.length > 0 && (
            <p className="text-sm text-muted">
              Váš feedback: odesláno k {done} z {variants.length} variant.
            </p>
          )}
          {login && <p className="rounded-md bg-soft p-3 text-sm">{login}</p>}
          <Link to={`/${slug}/compare`} className="pf-button w-full sm:w-auto">Otevřít varianty</Link>
        </section>
      )}
      {(data.variants_dropped?.length ?? 0) > 0 && (
        <p className="text-sm text-muted">
          Po Iterate pokračují varianty {(data.variants_in_play ?? []).join(", ")};
          varianta {data.variants_dropped!.join(", ")} vypadla (jen pro informaci).
        </p>
      )}
      {!inAsync && !killed && variants.length > 0 && (
        <Link to={`/${slug}/compare`} className="pf-button-secondary w-full sm:w-auto">Zobrazit varianty</Link>
      )}

      {hyp && (
        <section className="pf-card space-y-1" aria-labelledby="hyp-h">
          <h2 id="hyp-h">Co chceme ověřit</h2>
          <p className="whitespace-pre-line"><Md text={hyp.text} />{hyp.scope ? <> {hyp.scope}</> : null}</p>
          {project.primary_lagging_metric && (
            <p className="text-sm text-muted">Podle čeho poznáme úspěch: <Md text={project.primary_lagging_metric} /></p>
          )}
          {project.kill_criteria && (
            <p className="text-sm text-muted">Kdy projekt zastavíme: <Md text={project.kill_criteria} /></p>
          )}
        </section>
      )}

      <section className="pf-card space-y-3" aria-labelledby="steps-h">
        <h2 id="steps-h">Kroky cesty a kdo za ně odpovídá</h2>
        <ul className="grid gap-2 sm:grid-cols-2">
          {PATH_STEPS.map(([k, label]) => {
            const owner = owners[k];
            const me = !!owner && identity?.name === owner;
            return (
              <li key={k} className="rounded-md border border-line px-3 py-2">
                <span className="block text-sm text-muted">{label}</span>
                <span className="font-semibold">{ownerLabel(owner, confirmer) ?? "— nepřiřazeno"}</span>
                {me && <>{" "}<span className="pf-pill ml-1">to jste vy</span></>}
              </li>
            );
          })}
        </ul>
        {project.decider_name && (
          <p className="text-sm text-muted">Rozhoduje: <strong className="text-ink">{project.decider_name}</strong></p>
        )}
      </section>

      <details className="pf-card">
        <summary className="pf-summary">Detail projektu</summary>
        <div className="mt-3 space-y-5">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
            <KeyValue k="Sponzor" v={project.sponsor_name} />
            <KeyValue k="Úroveň AI Act" v={project.ai_act_tier} />
            <KeyValue k="Třída dat" v={project.data_class} />
            <KeyValue k="Zahodit / rozvíjet" v={project.throwaway_or_evolve} />
            <KeyValue k="Kapacita" v={`${project.capacity_profile || "—"} · ${project.capacity_person_days || 0} PD`} />
          </div>
          {roles.length > 0 && (
            <div className="overflow-x-auto">
              <h3 className="mb-2">Role v místnosti ({roles.length})</h3>
              <table className="w-full text-sm">
                <caption className="sr-only">Role v místnosti</caption>
                <thead className="text-left text-muted border-b border-line">
                  <tr><th scope="col" className="py-2">#</th><th scope="col">Role</th>
                    <th scope="col">Stav</th><th scope="col">Zástupce</th></tr>
                </thead>
                <tbody>
                  {roles.map((r) => (
                    <tr key={r.id} className="border-b border-line">
                      <td className="py-2 font-mono">{r.catalog_idx}</td>
                      <td>{r.catalog_label}</td>
                      <td>{r.status}</td>
                      <td>{r.human_owner || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {triage.length > 0 && (
            <div>
              <h3 className="mb-2">Předběžné kontroly</h3>
              <ul className="grid gap-2 md:grid-cols-2">
                {triage.map((t) => (
                  <li key={t.id} className="rounded border border-line p-3 text-sm">
                    <span className="font-semibold">{t.track}</span> · {t.status}
                    <span className="block text-muted">Podepsal(a): {t.signed_by || "—"}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </details>
    </div>
  );
}

function KeyValue({ k, v }: { k: string; v: ReactNode }) {
  return (
    <div>
      <div className="text-muted">{k}</div>
      <div className="font-semibold">{v || "—"}</div>
    </div>
  );
}
