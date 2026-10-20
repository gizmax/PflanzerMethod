import type { ReactNode } from "react";

/** Minimální render markdownu z DB: **tučné**, jinak prostý text bez značek. */
export function Md({ text }: { text: string }): ReactNode {
  const clean = text
    .replace(/([.!?])\*\*\.(?!\.)/g, "$1**")
    .replace(/^#{1,6}\s+/gm, "")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/^\s*[-*]\s+/gm, "• ");
  const parts = clean.split(/\*\*(.+?)\*\*/g);
  return (
    <>
      {parts.map((p, i) => (i % 2 === 1 ? <strong key={i}>{p}</strong> : <span key={i}>{p}</span>))}
    </>
  );
}

/** Zástupce kroku může být AI: "AI:ux-expert" -> "AI (ux-expert) — potvrzuje Petr". */
export function ownerLabel(owner: string | null | undefined, confirmer?: string | null): string | null {
  if (!owner) return null;
  const m = /^AI(?::\s*(.+))?$/i.exec(owner.trim());
  if (!m) return owner;
  const base = m[1] ? `AI (${m[1]})` : "AI";
  return confirmer ? `${base} — potvrzuje ${confirmer}` : base;
}

export function stripMd(text: string): string {
  return text.replace(/\*\*|__|`|^#{1,6}\s+/gm, "").trim();
}

/** Fáze projektu lidsky (status v DB je interní). */
export function phaseLabel(status: string, buildRunning = false): string {
  switch (status) {
    case "draft":
    case "charter":
      return "Kickoff — zadání se připravuje";
    case "triage":
      if (buildRunning) return "Build běží — varianty se ukážou po zápisu Buildu (`pflanzer record`)";
      return "Kickoff hotový — čeká se na Build";
    case "session_1":
      return "Async — čekáme na váš feedback";
    case "session_2":
      return "Rozhodnutí — vyhodnocuje se feedback";
    case "handoff":
      return "Předání — varianta byla vybrána";
    case "killed":
      return "Ukončeno";
    default:
      return status;
  }
}

export const SEVERITY: Record<string, { label: string; hint: string }> = {
  critical: { label: "Kritické (blokuje nasazení)", hint: "Nesmí se nasadit (právo, bezpečnost, data, rozbitý hlavní tok)" },
  high: { label: "Důležité", hint: "Opravit před spuštěním" },
  // medium se zobrazuje stejně jako low (starší záznamy); formulář nabízí jen critical/high/low
  medium: { label: "Drobné", hint: "Kosmetika, oprava v dalším kole" },
  low: { label: "Drobné", hint: "Kosmetika, oprava v dalším kole" },
};

export function formatDate(iso: string): string {
  const d = new Date(iso);
  return isNaN(d.getTime()) ? iso : d.toLocaleDateString("cs-CZ");
}
