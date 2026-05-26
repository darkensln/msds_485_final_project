/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        finguard: {
          navy:  '#0B1D3A',
          teal:  '#028090',
          mint:  '#02C39A',
          accent:'#F4A261',
          red:   '#E63946',
        },
      },
    },
  },
  plugins: [],
};
