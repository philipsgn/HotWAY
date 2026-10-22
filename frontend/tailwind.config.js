/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'app': '#FBF6EA',
        'surface': '#FFFDF7',
        'sunken': '#F3EAD6',
        'subtle': '#EFE4CD',
        'border-warm': '#E6D9BC',
        'primary-text': '#3B2A1A',
        'secondary-text': '#8A7355',
        'brand-gold': {
          DEFAULT: '#E0A83A',
          hover: '#C98F22',
          pressed: '#B07A18',
          soft: '#FBE9B7',
        },
        'brand-brown': '#8B5E34',
        'status-success': '#4E8F5A',
        'status-warning': '#D98A1F',
        'status-danger': '#C2493D',
        'route-1': '#2563eb',
        'route-2': '#d97706',
        'route-3': '#059669',
        'route-4': '#7c3aed',
        'route-5': '#dc2626',
        'route-6': '#0891b2',
      },
      fontFamily: {
        sans: ['Be Vietnam Pro', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      borderRadius: {
        'warm': '16px',
        'warm-lg': '20px',
      },
      boxShadow: {
        'soft': '0 4px 20px -2px rgba(59, 42, 26, 0.08)',
        'elevated': '0 12px 36px -4px rgba(59, 42, 26, 0.12), 0 4px 12px rgba(59, 42, 26, 0.06)',
        'floating': '0 16px 40px -6px rgba(59, 42, 26, 0.16)',
      },
    },
  },
  plugins: [],
};
