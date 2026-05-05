import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import type { Project } from "../lib/types";

export default function ProjectsList() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.listProjects().then(setProjects).catch((e) => setError(String(e)));
  }, []);

  if (error) return <div className="pf-card text-severity-critical">Chyba: {error}</div>;
  if (!projects.length) {
    return (
      <div className="pf-card">
        <h1>Pflanzer projekty</h1>
        <p className="mt-2 text-brand-500">
          Žádné projekty zatím nejsou. Spusť v Claude Code:{" "}
          <code className="font-mono bg-brand-50 px-1.5 py-0.5 rounded">
            /pflanzer-charter &lt;slug&gt;
          </code>
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h1>Pflanzer projekty ({projects.length})</h1>
      <div className="grid gap-3 md:grid-cols-2">
        {projects.map((p) => (
          <Link key={p.id} to={`/${p.slug}`} className="pf-card hover:border-brand-700 block">
            <div className="flex items-start justify-between mb-2">
              <h2 className="text-base">{p.name}</h2>
              <span className="text-xs font-mono px-2 py-0.5 bg-brand-50 rounded">
                {p.status}
              </span>
            </div>
            <p className="text-xs font-mono text-brand-500 mb-2">{p.slug}</p>
            {p.xyz_hypothesis && (
              <p className="text-sm text-brand-700 line-clamp-3">{p.xyz_hypothesis}</p>
            )}
          </Link>
        ))}
      </div>
    </div>
  );
}
