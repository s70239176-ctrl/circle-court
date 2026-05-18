/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        court: {
          ink: "#0f172a",
          panel: "#151922",
          line: "#2a3141",
          mint: "#3ddc97",
          gold: "#f4c95d",
          coral: "#ff6b6b"
        }
      }
    }
  },
  plugins: []
};
