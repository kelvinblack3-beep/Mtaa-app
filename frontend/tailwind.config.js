/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        forest: {
          50: '#f0f7f4',
          100: '#dceee6',
          200: '#bcdcce',
          300: '#8fc4ae',
          400: '#5ea68a',
          500: '#3d8a6e',
          600: '#2d6f58',
          700: '#255a48',
          800: '#1f483b',
          900: '#1a3b31',
          950: '#0d211c',
        },
        gold: {
          400: '#e4c065',
          500: '#d4a84b',
          600: '#b88a2e',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
