import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import type { Project } from "../lib/types";
import { ErrorScreen, Loading, StateScreen } from "../components/StateScreen";
import { phaseLabel, stripMd } from "../lib/text";
import { usePageTitle } from "../lib/hooks";

export default function ProjectsList() {
  usePageTitle("Projekty");
  const [projects, setProjects] = useState<Project[] | null>(null);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    api.listProjects().then(setProjects).catch(setError);
  }, []);

  if (error) return <ErrorScreen error={error} />;
  if (!projects) return <Loading />;
  if (!projects.length) {
    return (
      <StateScreen title="Zatím tu není žádný projekt" backLabel="Obnovit">
        <p>Projekt zakládá facilitátor na Kickoffu. Až bude hotový, dostanete na něj odkaz.</p>
      </StateScreen>
    );
  }

  return (
    <div className="space-y-4">
      <h1>Projekty ({projects.length})</h1>
      <ul className="grid gap-3 md:grid-cols-2">
        {projects.map((p) => (
          <li key={p.id}>
            <Link to={`/${p.slug}`} className="pf-card block h-full hover:border-accent">
              <h2 className="text-lg">{p.name}</h2>
              <p className="pf-pill mt-2">{phaseLabel(p.status)}</p>
              {p.xyz_hypothesis && (
                <p className="mt-2 text-sm text-muted line-clamp-3">{stripMd(p.xyz_hypothesis)}</p>
              )}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
