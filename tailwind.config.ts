import type { Config } from "tailwindcss";
const config: Config = {
  darkMode: "class",
  content: [
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#14143A", signal: "#4F46E5", paper: "#F7F7FB",
        ok: "#10B981", warn: "#F59E0B", bad: "#EF4444",
      },
      fontFamily: { display: ["var(--font-display)"], sans: ["var(--font-body)"] },
      keyframes: { pulseRing: { "0%": { transform: "scale(.9)", opacity: ".7" }, "100%": { transform: "scale(1.8)", opacity: "0" } } },
      animation: { ring: "pulseRing 2.4s ease-out infinite" },
    },
  },
  plugins: [],
};
export default config;
