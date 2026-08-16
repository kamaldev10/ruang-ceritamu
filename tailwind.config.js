/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/templates/**/*.html"],
  theme: {
    extend: {
      colors: {
        primary: "#0A3622",
        "primary-light": "#0D422A",
        brand: {
          50: "#EAF6EF", 100: "#CDEADA", 200: "#9BD5B7", 300: "#67BB92",
          400: "#3B9A72", 500: "#227A57", 600: "#176248", 700: "#124B38",
          800: "#0D3B29", 900: "#0A3622"
        },
        accent: { DEFAULT: "#C8F31D", hover: "#B8E312", soft: "#E6FA8C" },
        surface: "#F9F9F8",
        "on-surface": "#1A1C1C",
        "on-surface-variant": "#444945",
        error: "#BA1A1A",
        "error-container": "#FFDAD6"
      },
      borderRadius: { custom: "2rem", soft: "1.25rem" },
      boxShadow: {
        soft: "0 4px 20px -2px rgba(0, 0, 0, 0.04)",
        float: "0 10px 30px -5px rgba(0, 0, 0, 0.08)",
        glow: "0 0 20px rgba(200, 243, 29, 0.4)"
      },
      fontFamily: {
        heading: ["Be Vietnam Pro", "sans-serif"],
        body: ["Inter", "sans-serif"]
      },
      spacing: {
        "margin-desktop": "40px",
        "margin-mobile": "16px",
        "container-max-width": "1200px"
      },
      animation: {
        "fade-in": "fadeIn 0.4s ease-out forwards",
        "slide-up": "slideUp 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards"
      },
      keyframes: {
        fadeIn: { "0%": { opacity: "0" }, "100%": { opacity: "1" } },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(15px)" },
          "100%": { opacity: "1", transform: "translateY(0)" }
        }
      }
    }
  },
  plugins: [
    require("@tailwindcss/forms"),
    require("@tailwindcss/container-queries")
  ]
};
