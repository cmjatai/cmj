import path from 'path'

import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import inject from '@rollup/plugin-inject'

// Configuração separada do vite.config.js: os testes não usam o PWA, o ESLint nem o Tailwind.
export default defineConfig({
  plugins: [
    vue(),
    inject({
      '_': 'lodash',
      include: ['src/**/*.js', 'src/**/*.vue']
    })
  ],
  resolve: {
    alias: {
      '~@': path.resolve('./src')
    }
  },
  test: {
    environment: 'jsdom',
    include: ['tests/**/*.spec.js'],
    setupFiles: ['tests/setup.js'],
    css: false,
    restoreMocks: true
  }
})
