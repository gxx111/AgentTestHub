import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/hooks/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        app: {
          bg: "#f6f7f9",
          surface: "#ffffff",
          subtle: "#f9fafb",
          line: "#e5e7eb",
          lineStrong: "#d1d5db",
          text: "#0f172a",
          muted: "#64748b",
        },
        sidebar: {
          DEFAULT: "#0b1220",
          subtle: "#111a2e",
          line: "#1e293b",
          muted: "#94a3b8",
        },
        brand: {
          DEFAULT: "#2563eb",
          hover: "#1d4ed8",
          soft: "#eff6ff",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Microsoft YaHei",
          "sans-serif",
        ],
        mono: ["ui-monospace", "SFMono-Regular", "Consolas", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
