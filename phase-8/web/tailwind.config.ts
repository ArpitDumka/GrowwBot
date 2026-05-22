import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        groww: {
          DEFAULT: "#00D09C",
          bright: "#10E8B0",
          dark: "#00B386",
        },
        app: {
          bg: "#0B1219",
          main: "#0F1623",
          sidebar: "#0B1219",
          surface: "#1A222E",
          border: "#2A3444",
          text: "#E8EDF5",
          muted: "#8B95A8",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
      },
    },
  },
  plugins: [],
};

export default config;
