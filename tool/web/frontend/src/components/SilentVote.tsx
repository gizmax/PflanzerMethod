import { FormEvent, useEffect, useState } from "react";
import { api } from "../lib/api";
import type { VoteChoice, VoteOut, VotesState } from "../lib/types";
import { CopyButton } from "./CopyButton";

const LABEL: Record<VoteChoice, string> = { go: "Go", iterate: "Iterate", kill: "Kill" };

function voteSummary(v: VoteOut): string {
  const extra = v.choice === "go" && v.winner ? `, vítěz ${v.winner}`
    : v.choice === "iterate" && v.iterate_variants?.length ? `, varianty ${v.iterate_variants.join(", ")}` : "";
  return `${LABEL[v.choice]}${extra}`;
}

/** Tiché hlasování před Rozhodnutím. Hub nezapisuje rozhodnutí, jen ukáže výsledek a příkaz. */
/** Srozumitelná česká hláška z chyby API (422 z FastAPI i prostý text). */
export function voteErrorText(e: unknown): string {
  const fallback = "Hlas se nepodařilo uložit. Zkuste to prosím znovu.";
  const m = e instanceof Error ? e.message : "";
  let detail: unknown;
  try { detail = JSON.parse(m).detail; } catch { return fallback; }
  if (typeof detail === "string" && detail.trim()) return detail;
  if (Array.isArray(detail)) {
    const fields = detail.map((d) => (Array.isArray(d?.loc) ? String(d.loc[d.loc.length - 1]) : ""));
    if (fields.includes("winner")) return "Vyberte vítěznou variantu";
    if (fields.includes("choice")) return "Vyberte Go, Iterate nebo Kill.";
    if (fields.includes("comment")) return "Komentář je příliš dlouhý (nejvýše 300 znaků).";
    return "Hlas obsahuje neplatné údaje. Zkontrolujte formulář.";
  }
  return fallback;
}

export function SilentVote({ slug, variants, identityName, compact = false }: {
  slug: string; variants: string[]; identityName: string | null; compact?: boolean;
}) {
  const [st, setSt] = useState<VotesState | null>(null);
  const [choice, setChoice] = useState<VoteChoice | "">("");
  const [winner, setWinner] = useState("");
  const [comment, setComment] = useState("");
  const [iter, setIter] = useState<string[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [winnerErr, setWinnerErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    // změna identity = čistý formulář; vlastní uložený hlas nové identity se načte níže
    setSt(null); setChoice(""); setWinner(""); setComment(""); setIter([]); setErr(null); setWinnerErr(null);
    if (!identityName) return;
    let cancelled = false;
    api.getVotes(slug).then((s) => {
      if (cancelled) return;
      setSt(s);
      if (s.mine) { setChoice(s.mine.choice); setWinner(s.mine.winner ?? ""); setComment(s.mine.comment);
        setIter(s.mine.iterate_variants ?? []); }
    }).catch(() => { if (!cancelled) setSt(null); });
    return () => { cancelled = true; };
  }, [slug, identityName]);

  if (!identityName) {
    if (compact) return null;
    return <p className="text-sm text-muted">Pro tiché hlasování se nejdřív vyberte nahoře („Kdo jste?“).</p>;
  }
  if (!st || !st.enabled) return null;

  async function run(fn: () => Promise<VotesState>): Promise<boolean> {
    setBusy(true); setErr(null); setWinnerErr(null);
    try { setSt(await fn()); return true; } catch (e) {
      setErr(voteErrorText(e));
    } finally { setBusy(false); }
    return false;
  }
  function submit(e: FormEvent) {
    e.preventDefault();
    if (!choice) { setErr("Vyberte Go, Iterate nebo Kill."); return; }
    if (choice === "go" && !winner) {
      setErr(null); setWinnerErr("Vyberte vítěznou variantu");
      document.getElementById("vote-winner")?.focus();
      return;
    }
    setWinnerErr(null);
    void run(() => api.castVote(slug, {
      choice, winner: choice === "go" ? winner : null, comment,
      iterate_variants: choice === "iterate" ? iter : [],
    }));
  }

  const idp = compact ? "vc" : "vf";
  const waiting = st.voters.filter((v) => !v.voted).map((v) => v.name);
  return (
    <section className={compact ? "pf-card border-accent space-y-3" : "pf-card space-y-3"}
      aria-labelledby={compact ? "vote-compact-h" : "vote-h"}>
      <h2 id={compact ? "vote-compact-h" : "vote-h"}>
        {compact ? "Hlasujte: Go / Iterate / Kill" : "Tiché hlasování před Rozhodnutím"}
      </h2>
      <p className="text-sm text-muted">
        {compact
          ? "Tiché hlasování: pošlete volbu a jednu větu, ostatní ji neuvidí, dokud nehlasují všichni nebo Decider hlasy neodkryje."
          : "Každý pošle svou volbu a jednu větu. Dokud nehlasují všichni (nebo Decider neodkryje hlasy), ostatní volby nejsou vidět. Decider hlasuje poslední. Hub nic nezapisuje do rozhodnutí."}
      </p>
      {!st.revealed && (
        <p className="text-sm">
          Hlasovalo {st.voters.length - waiting.length} z {st.voters.length}
          {waiting.length > 0 ? <> · čeká se na: {waiting.join(", ")}</> : null}.
          {st.is_decider && waiting.length > 0 ? <> Chybí {waiting.length} {waiting.length === 1 ? "hlas" : waiting.length < 5 ? "hlasy" : "hlasů"}.</> : null}
        </p>
      )}
      {st.can_vote && (
        <form onSubmit={submit} noValidate className="space-y-3">
          <fieldset>
            <legend className="pf-label">{st.is_decider ? "Vaše volba (Decider)" : "Vaše volba"}</legend>
            <div className="flex flex-wrap gap-3">
              {(Object.keys(LABEL) as VoteChoice[]).map((c) => (
                <label key={c} htmlFor={`${idp}-vote-${c}`} className="flex min-h-[44px] items-center gap-2">
                  <input id={`${idp}-vote-${c}`} type="radio" name="vote" value={c} checked={choice === c} onChange={() => setChoice(c)}
                    className="h-5 w-5 accent-[rgb(var(--c-accent))]" />
                  {LABEL[c]}
                </label>
              ))}
            </div>
          </fieldset>
          {choice === "go" && (
            <div>
              <label htmlFor="vote-winner" className="pf-label">Vítězná varianta</label>
              <select id="vote-winner" className="pf-input" value={winner} required
                aria-invalid={winnerErr ? true : undefined}
                aria-describedby={winnerErr ? "vote-winner-err" : undefined}
                onChange={(e) => { setWinner(e.target.value); setWinnerErr(null); }}>
                <option value="">— vyberte —</option>
                {variants.map((v) => <option key={v} value={v}>{v}</option>)}
              </select>
              {winnerErr && <p id="vote-winner-err" role="alert" className="pf-error">{winnerErr}</p>}
            </div>
          )}
          {choice === "iterate" && (
            <fieldset>
              <legend className="pf-label">Které varianty do dalšího kola (volitelné)</legend>
              <div className="flex flex-wrap gap-3">
                {variants.map((v) => (
                  <label key={v} className="flex min-h-[44px] items-center gap-2">
                    <input type="checkbox" checked={iter.includes(v)} className="h-5 w-5 accent-[rgb(var(--c-accent))]"
                      onChange={(e) => setIter(e.target.checked ? [...iter, v] : iter.filter((x) => x !== v))} />
                    {v}
                  </label>
                ))}
              </div>
            </fieldset>
          )}
          <div>
            <label htmlFor="vote-comment" className="pf-label">Proč, jednou větou</label>
            <input id="vote-comment" className="pf-input" value={comment} maxLength={300}
              onChange={(e) => setComment(e.target.value)} />
          </div>
          {err && <p role="alert" className="pf-error">{err}</p>}
          {st.mine && !st.revealed && (
            <p role="status" className="text-sm font-semibold">
              Váš hlas je uložený: {voteSummary(st.mine)}. Ostatní ho uvidí po odkrytí.
            </p>
          )}
          <button type="submit" className="pf-button" disabled={busy}>
            {st.mine ? "Změnit hlas" : "Odeslat hlas"}
          </button>
        </form>
      )}
      {!st.can_vote && st.mine && !st.revealed && (
        <p role="status" className="text-sm font-semibold">
          Váš hlas je uložený: {voteSummary(st.mine)}. Ostatní ho uvidí po odkrytí.
        </p>
      )}
      {st.is_decider && !st.revealed && (
        <p className="text-sm">Decider hlasuje až po odkrytí ostatních.</p>
      )}
      {st.can_reveal && (
        <button type="button" className="pf-button-secondary" disabled={busy}
          onClick={() => void run(() => api.revealVotes(slug))}>Odkrýt hlasy</button>
      )}
      {!st.is_decider && !st.revealed && !st.can_reveal && st.decider && (
        <p className="text-sm text-muted">Hlasy odkryje {st.decider}.</p>
      )}
      {st.revealed && (
        <div className="space-y-2">
          <h3>Výsledek</h3>
          {st.tally && (
            <p className="text-sm">Go {st.tally.go} · Iterate {st.tally.iterate} · Kill {st.tally.kill}</p>
          )}
          <ul className="space-y-1 text-sm">
            {st.votes.map((v, i) => (
              <li key={i}>
                <strong>{v.voter}</strong>: {LABEL[v.choice]}{v.winner ? ` (${v.winner})` : ""}{v.choice === "iterate" && v.iterate_variants?.length ? ` (${v.iterate_variants.join(", ")})` : ""}
                {v.comment ? ` — ${v.comment}` : ""}
              </li>
            ))}
          </ul>
          {!st.decider_voted && st.decider && (
            <p className="text-sm text-muted">Decider ({st.decider}) ještě nehlasoval.</p>
          )}
          {st.command && (
            <>
              <p className="text-sm">Rozhodnutí zapíše Decider příkazem (upravte důvod):</p>
              <pre className="overflow-x-auto rounded-md bg-soft p-3 text-sm whitespace-pre-wrap break-words"><code>{st.command}</code></pre>
              <CopyButton text={st.command} />
            </>
          )}
        </div>
      )}
    </section>
  );
}
