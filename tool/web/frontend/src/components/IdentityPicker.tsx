import { useState } from "react";
import { PATH_STEPS, setIdentity, stepLabel, type Identity } from "../lib/identity";

/** "Kdo jste?" — výběr ze jmen zástupců kroků cesty projektu (nebo ruční zadání). */
export function IdentityPicker(props: {
  owners: Record<string, string | null>;
  onPick: (id: Identity) => void;
}) {
  const entries = PATH_STEPS.filter(([k]) => props.owners[k]).map(
    ([k, label]) => ({ key: k, label, name: props.owners[k] as string })
  );
  const [manual, setManual] = useState(entries.length === 0);
  const [name, setName] = useState("");
  const [step, setStep] = useState("");
  const [err, setErr] = useState<string | null>(null);

  function pick(id: Identity) {
    setIdentity(id);
    props.onPick(id);
  }

  return (
    <section className="pf-card space-y-3" aria-labelledby="who-h">
      <h2 id="who-h">Kdo jste?</h2>
      <p className="pf-help">Podle toho podepíšeme váš feedback a předvyplníme váš krok cesty.</p>
      {!manual && (
        <ul className="grid gap-2 sm:grid-cols-2">
          {entries.map((e) => (
            <li key={e.key}>
              <button
                type="button"
                className="pf-button-secondary w-full !justify-start text-left"
                onClick={() => pick({ name: e.name, step: e.label })}
              >
                {e.name} · {e.label}
              </button>
            </li>
          ))}
          <li>
            <button type="button" className="pf-button-secondary w-full" onClick={() => setManual(true)}>
              Nejsem v seznamu
            </button>
          </li>
        </ul>
      )}
      {manual && (
        <form
          noValidate
          className="space-y-3"
          onSubmit={(e) => {
            e.preventDefault();
            if (!name.trim() || !step) {
              setErr("Napište své jméno a vyberte svůj krok cesty.");
              return;
            }
            pick({ name: name.trim(), step: stepLabel(step) });
          }}
        >
          <div>
            <label htmlFor="who-name" className="pf-label">Vaše jméno</label>
            <input id="who-name" className="pf-input" value={name} autoComplete="name"
              onChange={(e) => setName(e.target.value)} aria-describedby={err ? "who-err" : undefined} />
          </div>
          <div>
            <label htmlFor="who-step" className="pf-label">Váš krok cesty</label>
            <select id="who-step" className="pf-input" value={step} onChange={(e) => setStep(e.target.value)}>
              <option value="">— vyberte —</option>
              {PATH_STEPS.map(([k, l]) => <option key={k} value={k}>{l}</option>)}
            </select>
          </div>
          {err && <p id="who-err" role="alert" className="pf-error">{err}</p>}
          <button type="submit" className="pf-button">Pokračovat</button>
        </form>
      )}
    </section>
  );
}
