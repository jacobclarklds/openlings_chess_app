/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        chess: {
          // Primary brand colors
          primary: {
            50: '#f0f9ff',
            100: '#e0f2fe',
            200: '#bae6fd',
            300: '#7dd3fc',
            400: '#38bdf8',
            500: '#0ea5e9',
            600: '#0284c7',
            700: '#0369a1',
            800: '#075985',
            900: '#0c4a6e',
          },
          // Board theme - Light squares
          boardLight: {
            DEFAULT: '#f0d9b5',
            alt: '#eeeed2',
            modern: '#e8e8e8',
          },
          // Board theme - Dark squares
          boardDark: {
            DEFAULT: '#b58863',
            alt: '#769656',
            modern: '#4f4f4f',
          },
          // UI backgrounds
          surface: {
            DEFAULT: '#262421',
            light: '#ffffff',
            elevated: '#312e2b',
            panel: '#1a1715',
          },
          // Highlight colors
          highlight: {
            lastMove: '#cdd26a66',
            selected: '#14551e66',
            check: '#ff404066',
            premove: '#3e383066',
            legal: '#00000020',
          },
          // Annotation colors
          annotation: {
            red: '#ef4444',
            green: '#22c55e',
            blue: '#3b82f6',
            yellow: '#eab308',
            orange: '#f97316',
          },
          // Evaluation bar
          evaluation: {
            white: '#ffffff',
            black: '#1a1715',
            winning: '#22c55e',
            losing: '#ef4444',
          }
        }
      },
      fontFamily: {
        sans: ['"Inter"', 'system-ui', 'sans-serif'],
        display: ['"Poppins"', '"Inter"', 'sans-serif'],
        mono: ['"Roboto Mono"', 'monospace'],
      },
      fontSize: {
        'board-coord': '0.75rem',
        'move-number': '0.875rem',
        'piece-value': '0.625rem',
      },
      spacing: {
        'board-gap': '1.5rem',
      },
      boxShadow: {
        'board': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        'panel': '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
        'elevated': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
      },
      borderRadius: {
        'board': '0.375rem',
      },
      keyframes: {
        pulse: {
          '0%, 100%': { opacity: 1 },
          '50%': { opacity: 0.5 },
        }
      },
      animation: {
        pulse: 'pulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      }
    },
  },
  plugins: [],
}
