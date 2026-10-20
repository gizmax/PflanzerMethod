import { useEffect, useState } from "react";
import { api } from "../lib/api";
import type { MissingInfo } from "../lib/types";

/** „Chybí: Petr (Provoz), …“ — zástupci, kteří ještě nedali žádný feedback (jen ve sběru). */
export function MissingBanner({ slug, refreshKey }: { slug: string; refreshKey?: unknown }) {
  const [info, setInfo] = useState<MissingInfo | null>(null);
  useEffect(() => {
    api.getMissing(slug).then(setInfo).catch(() => setInfo(null));
  }, [slug, refreshKey]);
  if (!info?.collecting) return null;
  if (!info.text) {
    return <p className="text-sm text-muted">Feedback poslali všichni zástupci kroků.</p>;
  }
  return <p className="rounded-md bg-soft p-3 text-sm"><strong>{info.text}</strong></p>;
}
