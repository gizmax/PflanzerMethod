import { useEffect, useState } from "react";
import { getIdentity, setIdentity, type Identity } from "./identity";

export function usePageTitle(title: string): void {
  useEffect(() => {
    document.title = `${title} · Pflanzer Method`;
  }, [title]);
}

export function useIdentity(): [Identity | null, (id: Identity | null) => void] {
  const [id, setId] = useState<Identity | null>(() => getIdentity());
  return [id, (v) => { setIdentity(v); setId(v); }];
}

/** true na širokém displeji (desktop) — iframe s náhledem se na mobilu nenačítá. */
export function useIsDesktop(): boolean {
  const q = "(min-width: 1024px)";
  const [yes, setYes] = useState(() => window.matchMedia(q).matches);
  useEffect(() => {
    const m = window.matchMedia(q);
    const on = () => setYes(m.matches);
    m.addEventListener("change", on);
    return () => m.removeEventListener("change", on);
  }, []);
  return yes;
}
