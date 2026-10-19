import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { ApiError } from "../lib/api";

/** Celostránková zpráva (chyba, prázdný stav) s h1 a tlačítkem zpět. */
export function StateScreen(props: {
  title: string;
  children?: ReactNode;
  backTo?: string;
  backLabel?: string;
}) {
  return (
    <div className="pf-card max-w-xl space-y-3">
      <h1>{props.title}</h1>
      {props.children && <div className="text-muted">{props.children}</div>}
      <Link to={props.backTo ?? "/"} className="pf-button-secondary">
        {props.backLabel ?? "Zpět na přehled"}
      </Link>
    </div>
  );
}

/** Převede chybu z API na českou obrazovku. */
export function ErrorScreen({ error, backTo, backLabel }: {
  error: unknown; backTo?: string; backLabel?: string;
}) {
  const status = error instanceof ApiError ? error.status : 0;
  if (status === 401) {
    return (
      <StateScreen title="Nejste přihlášeni" backTo={backTo} backLabel={backLabel}>
        <p>Přihlášení vypršelo nebo chybí. Obnovte stránku (F5) a přihlaste se znovu,
          případně zadejte sdílené heslo, které jste dostali od týmu.</p>
      </StateScreen>
    );
  }
  if (status === 404) {
    return (
      <StateScreen title="Projekt nenalezen" backTo={backTo} backLabel={backLabel}>
        <p>Zkontrolujte odkaz, který jste dostali.</p>
      </StateScreen>
    );
  }
  return (
    <StateScreen title="Něco se nepovedlo" backTo={backTo} backLabel={backLabel}>
      <p>Stránku se nepodařilo načíst. Zkuste ji obnovit (F5); když to nepomůže, napište facilitátorovi.</p>
    </StateScreen>
  );
}

export function Loading() {
  return (
    <div className="pf-card" role="status">
      <h1 className="sr-only">Načítám</h1>
      Načítám…
    </div>
  );
}
