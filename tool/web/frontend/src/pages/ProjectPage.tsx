import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../lib/api";
import type { ProjectDetail } from "../lib/types";

export default function ProjectPage() {
  const { slug } = useParams<{ slug: string }>();
  const [data, setData] = useState<ProjectDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!slug) return;
    api.getProject(slug).then(setData).catch((e) => setError(String(e)));
  }, [slug]);

  if (error) return <div className="pf-card text-severity-critical">Chyba: {error}</div>;
  if (!data) return <div className="pf-card">Načítám…</div>;

  const { project, roles, triage } = data;

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1>{project.name}</h1>
          <p className="text-xs font-mono text-brand-500">
            {project.slug} · status: <strong>{project.status}</strong>
          </p>
        </div>
        <div className="flex gap-2">
          <Link to={`/${slug}/compare`} className="pf-button">Compare variants</Link>
        </div>
      </div>

      <div className="pf-card space-y-3">
        <h2>Charter</h2>
        {project.xyz_hypothesis && (
          <Section label="XYZ hypotéza" value={project.xyz_hypothesis} />
        )}
        <div className="grid grid-cols-2 gap-3 text-sm">
          <KeyValue k="Decider" v={project.decider_name || "—"} />
          <KeyValue k="Sponsor" v={project.sponsor_name || "—"} />
          <KeyValue k="AI Act tier" v={project.ai_act_tier || "—"} />
          <KeyValue k="Data class" v={project.data_class || "—"} />
          <KeyValue k="Throwaway / evolve" v={project.throwaway_or_evolve || "—"} />
          <KeyValue
            k="Kapacita"
            v={`${project.capacity_profile || "—"} · ${project.capacity_person_days || 0} PD`}
          />
        </div>
        {project.primary_lagging_metric && (
          <Section label="Primary lagging metric" value={project.primary_lagging_metric} />
        )}
        {project.leading_metric && (
          <Section label="Leading metric" value={project.leading_metric} />
        )}
        {project.kill_criteria && (
          <Section label="Kill criteria" value={project.kill_criteria} />
        )}
      </div>

      <div className="pf-card">
        <h2>Role v místnosti ({roles.length})</h2>
        <table className="mt-3 w-full text-sm">
          <thead className="text-left text-xs text-brand-500 border-b border-brand-50">
            <tr>
              <th className="py-2">#</th>
              <th>Role</th>
              <th>Status</th>
              <th>AI mode</th>
              <th>Owner</th>
            </tr>
          </thead>
          <tbody>
            {roles.map((r) => (
              <tr key={r.id} className="border-b border-brand-50/50">
                <td className="py-2 font-mono">{r.catalog_idx}</td>
                <td>{r.catalog_label}</td>
                <td>
                  <span className={statusPill(r.status)}>{r.status}</span>
                </td>
                <td className="font-mono text-xs">{r.ai_proxy_mode}</td>
                <td className="text-brand-500">{r.human_owner || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="pf-card">
        <h2>Pre-flight triage</h2>
        <div className="grid gap-2 mt-3 md:grid-cols-2">
          {triage.map((t) => (
            <div key={t.id} className="border border-brand-50 rounded p-3">
              <div className="flex items-center justify-between mb-1">
                <span className="font-medium">{t.track}</span>
                <span className={statusPill(t.status)}>{t.status}</span>
              </div>
              <p className="text-xs text-brand-500">Signed by: {t.signed_by || "—"}</p>
            </div>
          ))}
          {triage.length === 0 && (
            <p className="text-brand-500 text-sm">
              Triage zatím neproběhla. V Claude Code:{" "}
              <code className="font-mono bg-brand-50 px-1.5 py-0.5 rounded">
                /pflanzer-triage {slug}
              </code>
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

function Section({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xs uppercase tracking-wide text-brand-500 mb-1">{label}</div>
      <div className="text-sm whitespace-pre-line">{value}</div>
    </div>
  );
}

function KeyValue({ k, v }: { k: string; v: string }) {
  return (
    <div>
      <div className="text-xs text-brand-500">{k}</div>
      <div className="font-medium">{v}</div>
    </div>
  );
}

function statusPill(status: string): string {
  const base = "text-xs font-mono px-2 py-0.5 rounded";
  switch (status) {
    case "ok":
    case "mandatory":
    case "recommended":
      return `${base} bg-severity-low/20 text-severity-low`;
    case "blocked":
    case "killed":
      return `${base} bg-severity-critical/20 text-severity-critical`;
    case "deferred":
    case "warning":
      return `${base} bg-severity-medium/20 text-severity-high`;
    default:
      return `${base} bg-brand-50 text-brand-700`;
  }
}
