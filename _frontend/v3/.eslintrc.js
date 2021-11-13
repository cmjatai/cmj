module.exports = {
  root: true,
  env: {
    node: true,
    browser: true
  },
  extends: [
    'eslint:recommended',
    'plugin:vue/vue3-strongly-recommended',
    // "plugin:prettier/recommended",
    'prettier',
    '@vue/prettier'
  ],
  parser: 'vue-eslint-parser',

  parserOptions: {
    parser: '@babel/eslint-parser',
    sourceType: 'module'
  },
  plugins: ['vue'],
  rules: {
    'prettier/prettier': [
      'warn',
      {
        singleQuote: true,
        semi: false,
        trailingComma: 'none'
      }
    ],
    'no-console': process.env.NODE_ENV === 'production' ? 'error' : 'off',
    'no-debugger': process.env.NODE_ENV === 'production' ? 'error' : 'off',
    'vue/require-default-prop': 'on'
  },
  globals: {}
}
