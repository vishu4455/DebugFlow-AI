/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: {
          900: "#060b18",
          800: "#0a0f1e",
          700: "#0d1428",
          600: "#111a35",
          500: "#1a2545",
          400: "#243060",
        },
        accent: {
          blue: "#3b72f8",
          "blue-dim": "#1e3a8a",
          green: "#3dd68c",
          "green-dim": "#0a2018",
          amber: "#f5a623",
          "amber-dim": "#2a1a08",
          red: "#e85d75",
          "red-dim": "#2a0d14",
        },
        border: "#1e2a45",
      },
      fontFamily: {
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      animation: {
        "pulse-slow": "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "spin-slow": "spin 1s linear infinite",
        "fade-in": "fadeIn 0.3s ease-out",
        "slide-up": "slideUp 0.3s ease-out",
      },
      keyframes: {
        fadeIn: { from: { opacity: 0 }, to: { opacity: 1 } },
        slideUp: { from: { opacity: 0, transform: "translateY(8px)" }, to: { opacity: 1, transform: "translateY(0)" } },
      },
    },
  },
  plugins: [],
};
