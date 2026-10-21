/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        chess: {
          dark: '#b58863',
          light: '#f0d9b5',
          highlight: 'rgba(255, 255, 0, 0.4)',
          selected: 'rgba(20, 85, 30, 0.5)',
          check: 'rgba(255, 0, 0, 0.55)',
          boardBorder: '#4a2e18'
        }
      }
    },
  },
  plugins: [],
}
