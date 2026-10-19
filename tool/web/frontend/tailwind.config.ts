import type { Config } from "tailwindcss";

const c = (name: string) => `rgb(var(--c-${name}) / <alpha-value>)`;

// Barvy jsou CSS proměnné (index.css) — světlý i tmavý režim (prefers-color-scheme).
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        page: c("page"),
        card: c("card"),
        line: c("line"),
        ink: c("ink"),
        muted: c("muted"),
        accent: c("accent"),
        "accent-ink": c("accent-ink"),
        soft: c("soft"),
        sev: {
          critical: c("sev-critical"),
          high: c("sev-high"),
          medium: c("sev-medium"),
          low: c("sev-low"),
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
} satisfies Config;
