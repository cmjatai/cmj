const vuePlugin = require('@vitejs/plugin-vue')
const eslintPlugin = require('vite-plugin-eslint')
console.log(eslintPlugin)
module.exports = {
  plugins: [vuePlugin(), eslintPlugin()],
  build: {
    minify: false
  }
}
