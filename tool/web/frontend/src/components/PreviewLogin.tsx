import { useState } from "react";
import type { ProjectDetail } from "../lib/types";
import { previewLoginText } from "../lib/task";

/** Přihlášení k náhledu. Heslo (pokud ho hub smí ukázat) je skryté za tlačítkem. */
export function PreviewLogin({ detail }: { detail: ProjectDetail }) {
  const [shown, setShown] = useState(false);
  const l = detail.preview_login;
  if (!l) return null;
  if (!l.password) {
    return <p className="rounded-md bg-soft p-3 text-sm">{previewLoginText(detail)}</p>;
  }
  return (
    <div className="rounded-md bg-soft p-3 text-sm space-y-2">
      <p>Náhled se otevře po přihlášení: uživatel <strong>{l.user}</strong>.</p>
      {shown ? (
        <p>Heslo: <code className="select-all">{l.password}</code></p>
      ) : null}
      <button type="button" className="pf-button-secondary" aria-expanded={shown}
        onClick={() => setShown(!shown)}>
        {shown ? "Skrýt heslo" : "Zobrazit heslo"}
      </button>
      <p className="text-muted">Heslo k náhledům — neposílejte ho dál mimo tým.</p>
    </div>
  );
}
