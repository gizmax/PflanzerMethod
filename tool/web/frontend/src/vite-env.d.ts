/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Dev-mode identity sent as X-User (ignored by the backend in OIDC mode). */
  readonly VITE_PFLANZER_DEV_USER?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
