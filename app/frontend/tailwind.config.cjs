const colors = {
  'primary-1': 'var(--aime-color-brand-1)',
  'primary-2': 'var(--aime-color-brand-2)',
  'primary-3': 'var(--aime-color-brand-3)',
  'primary-4': 'var(--aime-color-brand-4)',
  'primary-5': 'var(--aime-color-brand-5)',
  'primary-6': 'var(--aime-color-brand-6)',
  'primary-7': 'var(--aime-color-brand-7)',
  'primary-8': 'var(--aime-color-brand-8)',
  'primary-9': 'var(--aime-color-brand-9)',
  'primary-10': 'var(--aime-color-brand-10)',
  'gray-1': 'var(--aime-color-gray-1)',
  'gray-2': 'var(--aime-color-gray-2)',
  'gray-3': 'var(--aime-color-gray-3)',
  'gray-4': 'var(--aime-color-gray-4)',
  'gray-5': 'var(--aime-color-gray-5)',
  'gray-6': 'var(--aime-color-gray-6)',
  'gray-7': 'var(--aime-color-gray-7)',
  'gray-8': 'var(--aime-color-gray-8)',
  'gray-9': 'var(--aime-color-gray-9)',
  'gray-10': 'var(--aime-color-gray-10)',
  'color-1': 'var(--aime-color-text-base-1)',
  'color-2': 'var(--aime-color-text-base-2)',
  'color-3': 'var(--aime-color-text-base-3)',
  'color-4': 'var(--aime-color-text-base-disable)',
  'color-5': 'var(--aime-color-text-white)',
};

module.exports = {
  content: ['./src/**/*.{ts,tsx,js,jsx}'],
  darkMode: 'media',
  theme: {
    colors,
    animation: {
      'slide-in-up': '0.5s slide-in-up 0.5s ease-out both',
      'heart-beat': '2s heart-beat ease-in-out infinite',
    },
    keyframes: {
      'slide-in-up': {
        '0%': { transform: 'translateY(50px)', opacity: 0 },
        '100%': { transform: 'translateY(0)' },
      },
      'heart-beat': {
        '0%': { transform: 'scale(1)' },
        '14%': { transform: 'scale(1.05)' },
        '28%': { transform: 'scale(1)' },
        '42%': { transform: 'scale(1.15)' },
        '70%': { transform: 'scale(1)' },
      },
    },
  },
  variants: {
    extend: {
      backgroundColor: ['active'],
      margin: ['last', 'first'],
      padding: ['last', 'first'],
      borderWidth: ['first', 'last'],
      borderRadius: ['first', 'last'],
    },
  },
  plugins: [],
};
