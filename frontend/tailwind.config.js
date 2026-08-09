/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        paper: '#EEF0EA',
        'paper-line': '#C7CCC2',
        ink: '#1F2624',
        'ink-soft': '#4B534F',
        steel: '#35506B',
        'steel-soft': '#5A7690',
        stamp: {
          pass: '#2F6B4F',
          fail: '#B23A2E',
          hold: '#B8862E',
          conflict: '#6B4C8A',
        },
      },
      fontFamily: {
        mono: ['"IBM Plex Mono"', 'ui-monospace', 'monospace'],
        sans: ['"IBM Plex Sans"', 'ui-sans-serif', 'system-ui'],
      },
      backgroundImage: {
        grid: 'linear-gradient(#C7CCC2 1px, transparent 1px), linear-gradient(90deg, #C7CCC2 1px, transparent 1px)',
      },
      keyframes: {
        stampdown: {
          '0%': { opacity: '0', transform: 'scale(1.4) rotate(var(--stamp-rot, -4deg))' },
          '60%': { opacity: '1', transform: 'scale(0.94) rotate(var(--stamp-rot, -4deg))' },
          '100%': { opacity: '1', transform: 'scale(1) rotate(var(--stamp-rot, -4deg))' },
        },
      },
      animation: {
        stampdown: 'stampdown 240ms ease-out both',
      },
    },
  },
  plugins: [],
}
