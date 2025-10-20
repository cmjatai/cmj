import { defineConfig } from 'eslint/config'
import globals from 'globals'
import js from '@eslint/js'

import pluginVue from 'eslint-plugin-vue'
import skipFormatting from '@vue/eslint-config-prettier/skip-formatting'

export default defineConfig([
  {
    name: 'app/files-to-lint',
    files: ['./src/**/*.{js,mjs,jsx,vue}'],
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.node,
        // ...globals.browser,
        // ...globals.node,
        EventBus: 'readonly',
        bootstrap: 'readonly',
        // createBootstrap: 'readonly',
        $: 'readonly',
        jQuery: 'readonly',
        _: 'readonly',
       }
    },
  },
  {
    name: 'app/files-to-ignore',
    ignores: ['**/dist/**', '**/dist-ssr/**', '**/coverage/**'],
  },

  js.configs.recommended,

  skipFormatting,

  ...pluginVue.configs['flat/strongly-recommended'],

  {
    rules: {
      'vue/multi-word-component-names': 'off',
      'semi': ['error', 'never'],
      'quotes': ['error', 'single'],
      'comma-dangle': ['error', 'never'],
      'no-trailing-spaces': 'error',
      'no-multiple-empty-lines': ['error', { max: 1, maxEOF: 1 }],
      /*
      'object-curly-spacing': ['error', 'always'],
      'array-bracket-spacing': ['error', 'never'],
      'space-in-parens': ['error', 'never'],
      'space-before-blocks': ['error', 'always'],
      'keyword-spacing': ['error', { before: true, after: true }],
      'space-infix-ops': 'error',
      'eol-last': ['error', 'always'],
      'no-console': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
      'no-debugger': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
      'camelcase': 0,
      'vue/script-setup-uses-vars': 'error',
      'vue/no-mutating-props': 'error',
      'vue/require-default-prop': 'off',
      'vue/html-indent': ['error', 2], */
    }
  }
])
