/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["DM Sans", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      colors: {
        panel: "#0f1419",
        panel2: "#151c26",
        accent: "#3b82f6",
        line: "#2a3544",
      },
    },
  },
  plugins: [],
};
