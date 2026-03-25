// 📍 LOCATION: free-space/frontend/packages/config/tailwind/index.js
const { fontFamily } = require('tailwindcss/defaultTheme');

/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ['class'],
  content: [],
  theme: {
    extend: {
      colors: {
        // Brand palette — violet as primary (inclusive, non-binary)
        brand: {
          50:  '#f5f3ff',
          100: '#ede9fe',
          200: '#ddd6fe',
          300: '#c4b5fd',
          400: '#a78bfa',
          500: '#8b5cf6',
          600: '#7c3aed', // primary
          700: '#6d28d9',
          800: '#5b21b6',
          900: '#4c1d95',
          950: '#2e1065',
        },
        // Accent — pride pink
        pride: {
          red:    '#E40303',
          orange: '#FF8C00',
          yellow: '#FFED00',
          green:  '#008026',
          blue:   '#004DFF',
          violet: '#750787',
        },
        // Semantic aliases (consumed by components)
        primary:   'hsl(var(--primary))',
        secondary: 'hsl(var(--secondary))',
        accent:    'hsl(var(--accent))',
        muted:     'hsl(var(--muted))',
        background:'hsl(var(--background))',
        foreground:'hsl(var(--foreground))',
        border:    'hsl(var(--border))',
        input:     'hsl(var(--input))',
        ring:      'hsl(var(--ring))',
        destructive: {
          DEFAULT:    'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
      },
      fontFamily: {
        // Display — for headings, hero text
        display: ['var(--font-display)', ...fontFamily.sans],
        // Body — for reading content
        sans:    ['var(--font-body)', ...fontFamily.sans],
        // Mono — code
        mono:    ['var(--font-mono)', ...fontFamily.mono],
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
      animation: {
        'accordion-down': 'accordion-down 0.2s ease-out',
        'accordion-up':   'accordion-up 0.2s ease-out',
        'fade-in':        'fade-in 0.3s ease-out',
        'slide-up':       'slide-up 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
        'heart-pop':      'heart-pop 0.35s cubic-bezier(0.175, 0.885, 0.32, 1.275)',
        'skeleton-pulse': 'skeleton-pulse 1.5s ease-in-out infinite',
      },
      keyframes: {
        'accordion-down': {
          from: { height: '0' },
          to:   { height: 'var(--radix-accordion-content-height)' },
        },
        'accordion-up': {
          from: { height: 'var(--radix-accordion-content-height)' },
          to:   { height: '0' },
        },
        'fade-in': {
          from: { opacity: '0', transform: 'translateY(4px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
        'slide-up': {
          from: { opacity: '0', transform: 'translateY(20px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
        'heart-pop': {
          '0%':   { transform: 'scale(1)' },
          '50%':  { transform: 'scale(1.4)' },
          '100%': { transform: 'scale(1)' },
        },
        'skeleton-pulse': {
          '0%, 100%': { opacity: '1' },
          '50%':      { opacity: '0.4' },
        },
      },
      // Consistent z-index scale — avoid magic numbers in components
      zIndex: {
        base:    '0',
        raised:  '10',
        dropdown:'20',
        sticky:  '30',
        overlay: '40',
        modal:   '50',
        toast:   '60',
        tooltip: '70',
      },
    },
  },
  plugins: [
    require('tailwindcss-animate'),
    require('@tailwindcss/typography'),
    require('@tailwindcss/aspect-ratio'),
  ],
};
