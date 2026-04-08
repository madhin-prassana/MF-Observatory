/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#3b82f6',
        secondary: '#8b5cf6',
        'deep-space': '#0C1324',
        'glacial-base': '#151B2D',
        'arctic-sheet': '#191F31',
        'permafrost': '#23293C',
        'glacial-blue': '#ADC6FF',
        'electric-cyan': '#4CD7F6',
        'arctic-emerald': '#00E6A1',
        'warning-amber': '#FFB340',
        'critical-red': '#FF5C5C',
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'Inter', 'sans-serif'],
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
      },
    },
  },
  plugins: [],
}