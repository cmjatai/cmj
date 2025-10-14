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
    }
  }
])
