/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: { 50: '#eef7f2', 100: '#d7ece0', 600: '#1d7a4d', 700: '#16603c', 900: '#0d3b25' },
      },
    },
  },
  plugins: [],
}
