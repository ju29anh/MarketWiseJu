/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#edfffe',
          100: '#d7fffc',
          500: '#65c7bc',
          600: '#00827c',
          700: '#006b66',
          800: '#00514b',
          900: '#003734',
          950: '#011d1c',
        },
        surface: {
          50: '#edfffe',
          100: '#d9eeec',
          800: '#16433f',
          900: '#003734',
          950: '#012624',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      }
    },
  },
  plugins: [],
}
