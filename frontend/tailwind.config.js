/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    extend: {
      colors: {
        boon: {
          primary: 'var(--boon-primary)',
          'primary-light': 'var(--boon-primary-light)',
          'primary-bg': 'var(--boon-primary-bg)',
          'primary-dark': 'var(--boon-primary-dark)',
          accent: 'var(--boon-accent)',
          'text-primary': 'var(--boon-text-primary)',
          'text-secondary': 'var(--boon-text-secondary)',
          surface: 'var(--boon-surface)',
          'surface-alt': 'var(--boon-surface-alt)',
        },
      },
      fontFamily: {
        heading: ['Poppins', 'sans-serif'],
        body: ['Open Sans', 'sans-serif'],
      },
      minHeight: {
        touch: '44px',
      },
      minWidth: {
        touch: '44px',
      },
      spacing: {
        safe: 'env(safe-area-inset-bottom)',
      },
    },
  },
  plugins: [],
}
