import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// pflanzer.cz/method  — subpath base.
// Local dev na localhost:5173/method/...
export default defineConfig({
  plugins: [react()],
  base: "/method/",
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
  build: {
    outDir: "dist",
    sourcemap: true,
  },
});
