const vuePlugin = require("@vitejs/plugin-vue");

module.exports = {
  plugins: [vuePlugin()],
  build: {
    minify: false,
  },
};
