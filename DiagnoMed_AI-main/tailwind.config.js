/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  darkMode: 'class', // enable dark mode via a CSS class
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#3b82f6",
          hover: "#2563eb",
        },
        accent: {
          pink: "#ff6fa4",
          pink2: "#f26191",
          red: "#D63E31",
        },
        panel: {
          dark: "rgba(42, 37, 89, 0.9)",
          deep: "rgba(61, 53, 118, 0.95)",
        },
        text: {
          light: "#e0e0e0",
          blue: "#90cdf4",
        },
        success: "#4ade80",
        background: {
          gradient1: "#0f0c29",
          gradient2: "#302b63",
          gradient3: "#24243e",
        },
      },
    },
  },
  plugins: [],
};
