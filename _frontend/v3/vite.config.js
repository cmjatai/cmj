import { defineConfig } from 'vite'
import vuePlugin from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vuePlugin()]
})

// export const plugins = [vuePlugin(), eslintPlugin()]
// export const build = {
//   minify: false
// }
