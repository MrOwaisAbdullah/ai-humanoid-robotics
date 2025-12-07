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
        },
        // ChatGPT-style chat widget colors
        chat: {
          // Widget background
          bg: '#171717', // Dark ChatGPT background
          // User message background
          userBg: '#343541', // User message bubble
          // AI message background
          aiBg: 'transparent', // Transparent background for AI
          // Border colors
          border: '#4d4d4f',
          inputBg: '#40414f', // Input area background
          // Text colors
          userText: '#ececf1', // User message text
          aiText: '#ececf1', // AI message text
          mutedText: '#8e8ea0', // Muted/secondary text
          // Accent colors
          accent: '#10a37f', // ChatGPT green accent
          accentHover: '#0d8f6c', // Darker accent on hover
          // Status colors
          thinking: '#6b7280', // Thinking indicator gray
          error: '#ef4444', // Error red
          success: '#10b981', // Success green
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      borderRadius: {
        'DEFAULT': '0.25rem',
        'chat': '0.5rem', // ChatGPT-style rounded corners
        'chat-lg': '0.75rem', // Larger rounded corners for widget
        'pill': '9999px', // Pill shape for input area
      },
      boxShadow: {
        'chat': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        'chat-lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
        'thinking': '0 0 0 4px rgba(107, 114, 128, 0.3)', // Thinking indicator glow
      },
      animation: {
        'thinking-pulse': 'thinking 1.5s ease-in-out infinite',
        'cursor-blink': 'cursor 1s infinite',
        'slide-up': 'slideUp 0.2s ease-out',
      },
      keyframes: {
        thinking: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.5' },
        },
        cursor: {
          '0%, 50%': { opacity: '1' },
          '51%, 100%': { opacity: '0' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
  darkMode: ['class', '[data-theme="dark"]'], // Sync with Docusaurus data-theme
  screens: {
    // Add custom breakpoints for better chat widget responsiveness
    'chat-sm': '400px',
    'chat-md': '768px',
    'chat-lg': '1024px',
  },
}