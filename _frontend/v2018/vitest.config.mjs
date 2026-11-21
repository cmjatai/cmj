import path from 'path'

import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue2'
import inject from '@rollup/plugin-inject'

// Configuração só dos testes. O build e o dev server continuam com o Vue CLI (vue.config.js),
// que este arquivo não carrega: ele lê o .env do backend, e os testes não dependem dele.
// O que o webpack fornece e os testes precisam é repetido aqui: o alias `@`, os globais `$`,
// `jQuery` e `_` (ProvidePlugin). O compilador de templates (runtimeCompiler) entra em
// tests/setup.js.

// O vue-loader aceita `<template lang="html">`; o plugin do Vite trata qualquer `lang` como
// pré-processador. Como `html` é o padrão, o atributo sai antes de o plugin ler o arquivo.
const templateLangHtml = {
  name: 'v2018-template-lang-html',
  enforce: 'pre',
  transform (code, id) {
    if (id.endsWith('.vue') && code.includes('<template lang="html">')) {
      return { code: code.replace('<template lang="html">', '<template>'), map: null }
    }
  }
}

export default defineConfig({
  plugins: [
    templateLangHtml,
    vue(),
    inject({
      $: 'jquery',
      jQuery: 'jquery',
      _: 'lodash',
      include: ['src/**/*.js', 'src/**/*.vue']
    })
  ],
  resolve: {
    alias: {
      '@': path.resolve('./src')
    },
    // O webpack resolve `import X from './X'` para `X.vue`; o Vite só faz isso se for dito.
    extensions: ['.mjs', '.js', '.json', '.vue']
  },
  test: {
    environment: 'jsdom',
    include: ['tests/**/*.spec.js'],
    setupFiles: ['tests/setup.js'],
    css: false,
    restoreMocks: true
  }
})
