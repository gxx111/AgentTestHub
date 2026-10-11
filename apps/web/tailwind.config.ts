import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        obsidian: {
          950: "#050608",
          900: "#090A0F",
          850: "#0F111A",
          800: "#161926",
          700: "#22273B",
        },
        cyber: {
          cyan: "#00F2FE",
          azure: "#4FACFE",
        },
        emerald: {
          pulse: "#00E676",
        },
        crimson: {
          hazard: "#FF0055",
        },
        amber: {
          flame: "#FF9900",
        },
        violet: {
          verdict: "#7928CA",
          neon: "#B829EA",
        },
      },
      fontFamily: {
        sans: ["var(--font-geist-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-geist-mono)", "monospace"],
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "glow-cyan": "glowCyan 2s ease-in-out infinite alternate",
        "glow-red": "glowRed 2s ease-in-out infinite alternate",
      },
      keyframes: {
        glowCyan: {
          "0%": { boxShadow: "0 0 5px rgba(0, 242, 254, 0.2)" },
          "100%": { boxShadow: "0 0 20px rgba(0, 242, 254, 0.6)" },
        },
        glowRed: {
          "0%": { boxShadow: "0 0 5px rgba(255, 0, 85, 0.2)" },
          "100%": { boxShadow: "0 0 20px rgba(255, 0, 85, 0.6)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
