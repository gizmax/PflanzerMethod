import { useState } from "react";

/** Zkopíruje text do schránky; když schránka není k dispozici, text zůstane vybratelný vedle. */
export function CopyButton({ text, label = "Zkopírovat příkaz" }: { text: string; label?: string }) {
  const [state, setState] = useState<"idle" | "ok" | "fail">("idle");
  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      setState("ok");
    } catch {
      setState("fail");
    }
    window.setTimeout(() => setState("idle"), 2500);
  }
  return (
    <span className="inline-flex items-center gap-2">
      <button type="button" className="pf-button-secondary" onClick={copy}>{label}</button>
      <span role="status" className="text-sm text-muted">
        {state === "ok" ? "Zkopírováno ✓" : state === "fail" ? "Nešlo zkopírovat, označte text ručně." : ""}
      </span>
    </span>
  );
}
