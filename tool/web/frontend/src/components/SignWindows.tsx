import { useEffect, useState } from "react";
import { api } from "../lib/api";
import type { SignWindow } from "../lib/types";
import { CopyButton } from "./CopyButton";

/** Okna čekající na podpis: jméno podepisujícího + hotový příkaz. Hub nic nepodepisuje. */
export function SignWindows({ slug }: { slug: string }) {
  const [wins, setWins] = useState<SignWindow[] | null>(null);
  useEffect(() => {
    api.getWindows(slug).then((r) => setWins(r.windows)).catch(() => setWins(null));
  }, [slug]);
  if (!wins) return null;
  return (
    <section className="pf-card space-y-3" aria-labelledby="win-h">
      <h2 id="win-h">Okna čekající na podpis</h2>
      {wins.length === 0 ? <p className="text-sm text-muted">Všechna okna jsou podepsaná.</p> : (
        <ul className="space-y-3">
          {wins.map((w) => (
            <li key={w.window} className="rounded-md border border-line p-3 space-y-2">
              <p>
                <strong>{w.label}</strong>
                {w.state === "blocked" ? " (blokováno)" : ""} — podepisuje{" "}
                <strong>{w.signer ?? "zatím nikdo určený"}</strong>
              </p>
              <pre className="overflow-x-auto rounded-md bg-soft p-3 text-sm whitespace-pre-wrap break-words"><code>{w.command}</code></pre>
              <CopyButton text={w.command} />
            </li>
          ))}
        </ul>
      )}
      <p className="text-sm text-muted">Podpis jde jen přes CLI; hub příkaz jen připraví.</p>
    </section>
  );
}
