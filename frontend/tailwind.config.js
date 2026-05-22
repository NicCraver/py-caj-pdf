/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        surface: {
          light: '#ffffff',
          card: '#f8fafc',
          dark: '#0f1117',
          cardDark: '#1a1d27',
        },
        accent: {
          DEFAULT: '#2563eb',
          hover: '#1d4ed8',
        },
      },
      fontFamily: {
        sans: [
          'PingFang SC',
          'Microsoft YaHei',
          'system-ui',
          '-apple-system',
          'sans-serif',
        ],
      },
      boxShadow: {
        soft: '0 1px 3px rgba(15, 23, 42, 0.06), 0 8px 24px rgba(15, 23, 42, 0.04)',
      },
    },
  },
  plugins: [],
}
