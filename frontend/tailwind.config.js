/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // FBI/Dark government aesthetic
        vault: {
          950: '#0a0c10',
          900: '#111318',
          800: '#1a1d24',
          700: '#252a33',
          600: '#303642',
          500: '#3d4551',
        },
        // Official blue/cyan accent
        intel: {
          400: '#22d3ee',
          500: '#06b6d4',
          600: '#0891b2',
          700: '#0e7490',
        },
        // Security levels
        secure: '#059669',
          caution: '#d97706',
          threat: '#dc2626',
          critical: '#991b1b',
        },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Consolas', 'monospace'],
      },
      animation: {
        'scan': 'scan 3s linear infinite',
        'pulse-intel': 'pulseIntel 2s ease-in-out infinite',
        'fade-in': 'fadeIn 0.4s ease-out',
        'slide-up': 'slideUp 0.4s ease-out',
      },
      keyframes: {
        scan: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100vh)' },
        },
        pulseIntel: {
          '0%, 100%': { opacity: '1', boxShadow: '0 0 20px rgba(6, 182, 212, 0.3)' },
          '50%': { opacity: '0.8', boxShadow: '0 0 40px rgba(6, 182, 212, 0.6)' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      backgroundImage: {
        'grid-pattern': 'linear-gradient(to right, #1a1d24 1px, transparent 1px), linear-gradient(to bottom, #1a1d24 1px, transparent 1px)',
      },
    },
  },
  plugins: [],
}
