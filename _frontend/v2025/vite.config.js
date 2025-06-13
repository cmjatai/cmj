import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

import inject from "@rollup/plugin-inject";

// https://demo.viewflow.io/dashboard/oilngas/

/*import { viteStaticCopy } from 'vite-plugin-static-copy';
#viteStaticCopy({targets: copyTargets})],
const copyTargets = [
  {
    src: [
      `node_modules/shepherd.js/dist/js/shepherd.min.js`,
      `node_modules/shepherd.js/dist/js/shepherd.min.js.map`,
      `node_modules/js-cookie/dist/js.cookie.min.js`
    ],
    dest: '../../../demo/static/demo/js/',
  },*/


import Components from 'unplugin-vue-components/vite'
import {BootstrapVueNextResolver} from 'bootstrap-vue-next'

import {resolve} from 'path'

export default defineConfig(({command, mode}) => {
  // eslint-disable-next-line
  console.log(`configuring vite with command: ${command}, mode: ${mode}`);
  // suppress eslint warning that process isn't defined (it is)
  // eslint-disable-next-line
  const cwd = process.cwd();
  // eslint-disable-next-line
  console.log(`loading envs from ${cwd} ...`);

  const env = {...loadEnv(mode, cwd, 'VITE_')};
  // eslint-disable-next-line
  console.log(`loaded env: ${JSON.stringify(env)}`);

  // eslint-disable-next-line
  const BASE_DIR = './'
  const OUTPUT_DIR = './dist'
  const INPUT_DIR = './src'

  return {
    plugins: [
      inject({   // => that should be first under plugins array
        $: 'jquery',
        jQuery: 'jquery',
        '_': 'lodash',
      }),
      vue(),
      Components({
        resolvers: [
          BootstrapVueNextResolver({
            aliases: {
              //BInput: 'BFormInput',
            },
          }),
        ],
      }),
    ],
    resolve: {
      extensions: ['.js', '.json', '.vue',],
      alias: {
        '~@': resolve(INPUT_DIR),
        'vue': 'vue/dist/vue.esm-bundler.js',
      },
    },
    root: resolve(INPUT_DIR),
    base: '/static/',
    server: {
      host: '0.0.0.0',
      port: 5173,
      open: false,
      watch: {
        usePolling: true,
        disableGlobbing: false,
      },
    },
    publicDir: resolve(INPUT_DIR, 'assets'),
    build: {
      outDir: resolve(OUTPUT_DIR),
      assetsDir: '',
      manifest: true,
      emptyOutDir: true,
      copyPublicDir: true,
      target: 'es2015',
      rollupOptions: {
        input: {
          main: resolve(INPUT_DIR, 'main.js'),
        },
        output: {
          chunkFileNames: undefined,
          /*manualChunks: {
            'group1': [
              './_frontend/src/components/utils/message/Alert.vue',
            ],
            'group2': [
              './_frontend/src/components/utils/message/DisplayMessage.vue',
            ],
          },*/
        },
      },
    },
  }
})
