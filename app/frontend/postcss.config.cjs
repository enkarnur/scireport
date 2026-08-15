const path = require('path');

module.exports = {
  plugins: {
    '@tailwindcss/postcss': {
      config: path.resolve(__dirname, 'tailwind.config.cjs'),
    },
  },
};
