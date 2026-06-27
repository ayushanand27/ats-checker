import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        /* Approved design tokens */
        canvas: "#0B0C0F",
        surface: {
          DEFAULT: "#13151A",
          hover: "#181B22",
        },
        border: "#252830",
        text: {
          DEFAULT: "#E6E8ED",
          muted: "#7B8394",
        },
        accent: {
          DEFAULT: "#8B7355",
          foreground: "#0B0C0F",
        },
        /* Semantic (functional only) */
        pass: "rgba(74, 222, 128, 0.85)",
        fail: "#F87171",
        warn: "#FBBF24",
        score: {
          low: "#9B6B6B",
          mid: "#8B7355",
          high: "#6B8F7A",
        },
        /* shadcn aliases → same tokens */
        background: "#0B0C0F",
        foreground: "#E6E8ED",
        card: {
          DEFAULT: "#13151A",
          foreground: "#E6E8ED",
        },
        popover: {
          DEFAULT: "#13151A",
          foreground: "#E6E8ED",
        },
        primary: {
          DEFAULT: "#8B7355",
          foreground: "#0B0C0F",
        },
        secondary: {
          DEFAULT: "#181B22",
          foreground: "#E6E8ED",
        },
        muted: {
          DEFAULT: "#181B22",
          foreground: "#7B8394",
        },
        destructive: {
          DEFAULT: "#F87171",
          foreground: "#E6E8ED",
        },
        input: "#252830",
        ring: "#8B7355",
      },
      fontFamily: {
        sans: ["var(--font-plex)", "IBM Plex Sans", "system-ui", "sans-serif"],
        serif: ["var(--font-instrument)", "Instrument Serif", "Georgia", "serif"],
      },
      borderRadius: {
        DEFAULT: "6px",
        md: "6px",
        sm: "4px",
        lg: "8px",
      },
      maxWidth: {
        tool: "56rem",
      },
      transitionDuration: {
        micro: "150ms",
      },
    },
  },
  plugins: [],
};

export default config;
