import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../lib/api";
import type { Variant } from "../lib/types";

export default function CompareVariants() {
  const { slug } = useParams<{ slug: string }>();
  const [variants, setVariants] = useState<Variant[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!slug) return;
    api.listVariants(slug).then(setVariants).catch((e) => setError(String(e)));
  }, [slug]);

  if (error) return <div className="pf-card text-severity-critical">Chyba: {error}</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1>Variants — {slug}</h1>
        <Link to={`/${slug}`} className="pf-button-secondary">← Zpět na projekt</Link>
      </div>

      {variants.length === 0 ? (
        <div className="pf-card">
          <p className="text-brand-500">
            Žádné variants zatím nebyly publikovány. V Claude Code:{" "}
            <code className="font-mono bg-brand-50 px-1.5 py-0.5 rounded">
              /pflanzer-session-1 {slug}
            </code>
          </p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {variants.map((v) => (
            <article key={v.id} className="pf-card flex flex-col">
              <div className="flex items-start justify-between mb-2">
                <h2>Varianta {v.name}</h2>
                <span className="text-xs font-mono bg-brand-50 px-2 py-0.5 rounded">
                  {v.builder}
                </span>
              </div>
              {v.description_md && (
                <p className="text-sm text-brand-700 mb-3 line-clamp-4">{v.description_md}</p>
              )}
              {v.preference_score !== null && (
                <div className="text-xs text-brand-500 mb-3">
                  Preference score: <strong>{(v.preference_score ?? 0).toFixed(2)}</strong>
                </div>
              )}
              <div className="aspect-video bg-brand-50 rounded mb-3 overflow-hidden">
                <iframe
                  src={v.prototype_url}
                  title={`Variant ${v.name}`}
                  className="w-full h-full"
                  sandbox="allow-scripts allow-same-origin allow-forms"
                  loading="lazy"
                />
              </div>
              <div className="mt-auto flex gap-2">
                <a
                  href={v.prototype_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="pf-button-secondary flex-1 text-center"
                >
                  Otevřít v novém okně
                </a>
                <Link
                  to={`/${slug}/feedback/${v.id}`}
                  className="pf-button flex-1 text-center"
                >
                  Dát feedback
                </Link>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
