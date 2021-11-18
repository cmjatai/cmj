import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'


export default defineConfig(({ command, mode }) => {
  return {
    plugins: [
      vue(),
    ],
    clearScreen: false,
    envPrefix: 'V3_'
  }
})