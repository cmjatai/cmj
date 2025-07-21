module.exports = {
  root: true,
  env: {
    browser: true,
    node: true,
    jquery: true
  },
  'extends': [
    'plugin:vue/essential',
    '@vue/standard'
  ],
  rules: {
    'generator-star-spacing': 'off',
    // 'no-console': process.env.NODE_ENV === 'production' ? 'error' : 'off',
    'no-debugger': process.env.NODE_ENV === 'production' ? 'error' : 'off',
    camelcase: 0
  },
  plugins: [
    'vue'
  ],
  parserOptions: {
    parser: 'babel-eslint'
  },

  globals: {
    '$': true,
    'jQuery': true,
    '_': true
  }
}
