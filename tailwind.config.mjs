/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        bg: '#1a1a2e',
        surface: '#16213e',
        surface2: '#0f3460',
        teal: {
          DEFAULT: '#2C9AB7',
          light: '#4fc3f7',
          dark: '#1a6a82',
        },
        sage: {
          DEFAULT: '#4caf82',
          light: '#7dd4aa',
          dark: '#2d7a57',
        },
        amber: {
          DEFAULT: '#f6a623',
          light: '#ffc96b',
        },
        text: {
          primary: '#e8eaf0',
          muted: '#8892a4',
          faint: '#4a5568',
        },
      },
      fontFamily: {
        display: ['"Outfit"', 'sans-serif'],
        sans: ['"Outfit"', 'sans-serif'],
        serif: ['"Lora"', 'Georgia', 'serif'],
        mono: ['"Fira Code"', '"JetBrains Mono"', 'monospace'],
      },
      typography: (theme) => ({
        invert: {
          css: {
            '--tw-prose-body': theme('colors.text.primary'),
            '--tw-prose-headings': theme('colors.text.primary'),
            '--tw-prose-links': theme('colors.teal.DEFAULT'),
            '--tw-prose-bold': theme('colors.text.primary'),
            '--tw-prose-counters': theme('colors.text.muted'),
            '--tw-prose-bullets': theme('colors.teal.DEFAULT'),
            '--tw-prose-hr': theme('colors.surface2'),
            '--tw-prose-quotes': theme('colors.text.muted'),
            '--tw-prose-quote-borders': theme('colors.teal.DEFAULT'),
            '--tw-prose-captions': theme('colors.text.muted'),
            '--tw-prose-code': theme('colors.teal.light'),
            '--tw-prose-pre-code': theme('colors.text.primary'),
            '--tw-prose-pre-bg': theme('colors.surface'),
            '--tw-prose-th-borders': theme('colors.surface2'),
            '--tw-prose-td-borders': theme('colors.surface'),
          },
        },
      }),
      animation: {
        'topo-drift': 'topoDrift 20s ease-in-out infinite',
        'topo-drift-2': 'topoDrift2 25s ease-in-out infinite',
        'topo-drift-3': 'topoDrift3 30s ease-in-out infinite',
        'fade-up': 'fadeUp 0.6s ease-out forwards',
        'blink': 'blink 1s step-end infinite',
      },
      keyframes: {
        topoDrift: {
          '0%, 100%': { transform: 'translateY(0) translateX(0)', opacity: '0.18' },
          '33%': { transform: 'translateY(-12px) translateX(8px)', opacity: '0.28' },
          '66%': { transform: 'translateY(8px) translateX(-6px)', opacity: '0.15' },
        },
        topoDrift2: {
          '0%, 100%': { transform: 'translateY(0) translateX(0)', opacity: '0.12' },
          '50%': { transform: 'translateY(15px) translateX(-10px)', opacity: '0.22' },
        },
        topoDrift3: {
          '0%, 100%': { transform: 'translateY(0) scale(1)', opacity: '0.1' },
          '40%': { transform: 'translateY(-8px) scale(1.02)', opacity: '0.2' },
          '80%': { transform: 'translateY(6px) scale(0.98)', opacity: '0.08' },
        },
        fadeUp: {
          from: { opacity: '0', transform: 'translateY(24px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        blink: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0' },
        },
      },
    },
  },
  plugins: [require('@tailwindcss/typography')],
};
