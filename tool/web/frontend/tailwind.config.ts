import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Pflanzer brand — sober, governance-grade.
        brand: {
          50: "#f5f7f9",
          500: "#3b5b7e",
          700: "#27425e",
          900: "#16263a",
        },
        severity: {
          critical: "#b00020",
          high: "#d97706",
          medium: "#f59e0b",
          low: "#65a30d",
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
