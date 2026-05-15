/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        cream: '#FAF7F2',
        ink: '#1A1A1A',
        sage: '#7A8B7F',
        ochre: '#B8826B',
        muted: '#6B6660',
        line: '#E8E2D8',
      },
      fontFamily: {
        serif: ['Fraunces', 'Cormorant Garamond', 'Georgia', 'serif'],
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      typography: ({ theme }) => ({
        DEFAULT: {
          css: {
            color: theme('colors.ink'),
            maxWidth: '68ch',
            a: { color: theme('colors.ochre'), textDecoration: 'underline', textUnderlineOffset: '3px' },
            h1: { fontFamily: theme('fontFamily.serif').join(',') },
            h2: { fontFamily: theme('fontFamily.serif').join(','), marginTop: '2.4em' },
            h3: { fontFamily: theme('fontFamily.serif').join(',') },
            blockquote: { fontStyle: 'italic', borderLeftColor: theme('colors.sage') },
            'figure figcaption': { color: theme('colors.muted'), fontSize: '0.85em' },
            img: {
              borderRadius: '4px',
              display: 'block',
              marginLeft: 'auto',
              marginRight: 'auto',
              maxHeight: '70vh',
              width: 'auto',
              maxWidth: '100%',
            },
          },
        },
      }),
    },
  },
  plugins: [require('@tailwindcss/typography')],
};
