/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./scan.html",
    "./about.html",
    "./profile.html",
    "./result.html",
    "./test.html",
    "./src/**/*.{js,ts,jsx,tsx}",
    "./js/**/*.js"
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        "on-background": "var(--on-background)",
        surface: "var(--surface)",
        "on-surface": "var(--on-surface)",
        "surface-container": "var(--surface-container)",
        "surface-container-low": "var(--surface-container-low)",
        "surface-container-high": "var(--surface-container-high)",
        "surface-container-lowest": "var(--surface-container-lowest)",
        "surface-container-highest": "var(--surface-container-highest)",
        "surface-variant": "var(--surface-variant)",
        "outline-variant": "var(--outline-variant)",
        outline: "var(--outline)",
        "on-surface-variant": "var(--on-surface-variant)",
        "surface-dim": "var(--surface-dim)",
        
        primary: "rgb(var(--primary-rgb) / <alpha-value>)",
        secondary: "rgb(var(--secondary-rgb) / <alpha-value>)",
        error: "rgb(var(--error-rgb) / <alpha-value>)",
        success: "rgb(var(--success-rgb) / <alpha-value>)",

        /* Material Design 3 container/tonal tokens */
        "primary-container":    "var(--primary-container)",
        "on-primary-container": "var(--on-primary-container)",
        "secondary-container":  "var(--secondary-container)",
        "on-secondary-container": "var(--on-secondary-container)",
        "secondary-fixed-dim":  "var(--secondary-fixed-dim)",
        "error-container":      "var(--error-container)",
        "on-error-container":   "var(--on-error-container)",

        "dark-background": "#070a13",
        "dark-on-surface": "#f1f5f9",
      },
      borderRadius: {
        DEFAULT: "0.25rem", lg: "0.5rem", xl: "0.75rem", full: "9999px"
      },
      spacing: {
        xs: "0.25rem", sm: "0.5rem", md: "1rem", lg: "1.5rem", xl: "2.5rem", xxl: "4rem"
      },
      fontFamily: {
        "body-md": ["Inter", "sans-serif"], "label-sm": ["Inter", "sans-serif"], "headline-md": ["Plus Jakarta Sans", "sans-serif"],
        "body-lg": ["Inter", "sans-serif"], "display-lg": ["Plus Jakarta Sans", "sans-serif"],
        "headline-lg": ["Plus Jakarta Sans", "sans-serif"], "label-md": ["Inter", "sans-serif"], "label-lg": ["Inter", "sans-serif"]
      },
      fontSize: {
        "body-md": ["16px", { lineHeight: "1.6", fontWeight: "400" }],
        "label-sm": ["12px", { lineHeight: "1.2", fontWeight: "600" }],
        "headline-md": ["24px", { lineHeight: "1.4", fontWeight: "600" }],
        "body-lg": ["18px", { lineHeight: "1.6", fontWeight: "400" }],
        "display-lg": ["48px", { lineHeight: "1.2", letterSpacing: "-0.02em", fontWeight: "700" }],
        "headline-lg": ["32px", { lineHeight: "1.3", fontWeight: "600" }],
        "label-md": ["14px", { lineHeight: "1.2", letterSpacing: "0.01em", fontWeight: "500" }],
        "label-lg": ["16px", { lineHeight: "1.3", letterSpacing: "0.01em", fontWeight: "600" }]
      }
    }
  },
  plugins: []
}
