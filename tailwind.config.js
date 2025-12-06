/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/**/*.{js,jsx,ts,tsx,md,mdx}',
    './docs/**/*.{md,mdx}',
    './blog/**/*.{md,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Minimalist Palette Map
        primary: {
          light: '#18181b', // Zinc 900
          dark: '#fafafa',  // Zinc 50
        },
        background: {
          light: '#ffffff',
          dark: '#09090b', // Zinc 950
        },
        foreground: {
          light: '#18181b',
          dark: '#e4e4e7',
        },
        muted: {
          light: '#71717a',
          dark: '#a1a1aa',
        },
        border: {
          light: '#e4e4e7',
          dark: '#27272a',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      borderRadius: {
        'DEFAULT': '0.25rem',
      },
    },
  },
  plugins: [],
  darkMode: ['class', '[data-theme="dark"]'], // Sync with Docusaurus data-theme
}