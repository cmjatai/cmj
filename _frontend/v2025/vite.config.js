import { defineConfig, loadEnv } from 'vite'
import {BootstrapVueNextResolver} from 'bootstrap-vue-next'
import {resolve} from 'path'
import Components from 'unplugin-vue-components/vite'
import fs from 'fs'
import inject from "@rollup/plugin-inject"
import vue from '@vitejs/plugin-vue'
import eslintPlugin from '@nabla/vite-plugin-eslint'


export default defineConfig(({command, mode}) => {
  // eslint-disable-next-line
  console.debug(`configuring vite with command: ${command}, mode: ${mode}`)
  // suppress eslint warning that process isn't defined (it is)
  // eslint-disable-next-line
  const cwd = process.cwd()
  // eslint-disable-next-line
  console.debug(`loading envs from ${cwd} ...`)

  const env = {...loadEnv(mode, cwd, 'VITE_')}
  // eslint-disable-next-line
  console.debug(`loaded env: ${JSON.stringify(env)}`)

  // eslint-disable-next-line
  const BASE_DIR = '.'
  const OUTPUT_DIR = './dist/v2025'
  const INPUT_DIR = './src'

  return {
    plugins: [
      vue(),
      inject({   // => that should be first under plugins array
        $: 'jquery',
        jQuery: 'jquery',
        '_': 'lodash',
        include: ['src/**/*.js', 'src/**/*.vue'],
        exclude: 'src/routers/**'
      }),
      eslintPlugin({
        // include: ['src/**/*.js', 'src/**/*.vue'],
        exclude: ['node_modules/**', 'dist/**', 'dist-ssr/**', 'coverage/**'],
        cache: false,
        failOnWarning: false,
        failOnError: true,
        // fix: true,
        emitWarning: true,
        emitError: true,
      }),
      Components({
        resolvers: [
          BootstrapVueNextResolver({
            aliases: {
              //BInput: 'BFormInput',
            }
          })
        ]
      }),
      {
        name: 'postbuild-commands',
        closeBundle: () => {
          // eslint-disable-next-line
          if (command !== 'build') return;
          console.debug('Vite build finished!', mode === 'production' ? 'production mode' : 'development mode');
          const path = './dist/v2025/.vite/manifest.json';
          const manifest = JSON.parse(fs.readFileSync(path).toString());
          Object.keys(manifest).forEach(key => {
            if (manifest[key].file) {
              manifest[key].file = 'v2025/' + manifest[key].file;
            }
            if (manifest[key].css) {
              manifest[key].css = manifest[key].css.map(cssFile => 'v2025/' + cssFile);
            }
            if (manifest[key].assets) {
              manifest[key].assets = manifest[key].assets.map(assetFile => 'v2025/' + assetFile);
            }
          });
          // eslint-disable-next-line
          console.debug('Adjusted manifest:', manifest);
          // Write the updated manifest back to the file
          fs.writeFileSync(path, JSON.stringify(manifest, null, 2));
        }
      }
    ],
    resolve: {
      extensions: ['.js', '.json', '.vue',],
      alias: {
        '~@': resolve(INPUT_DIR),
        'vue': 'vue/dist/vue.esm-bundler.js',
      },
    },
    root: resolve(INPUT_DIR),
    base: '/static/v2025/',
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
    /* worker: {
      format: 'es',
      plugins: [],
    }, */
    build: {
      outDir: resolve(OUTPUT_DIR),
      assetsDir: '',
      manifest: true,
      emptyOutDir: true,
      copyPublicDir: true,
      target: 'esnext',
      minify: 'esbuild',
      esbuild: {
        pure: mode === 'production' ? ['console.debug'] : []
      },
      sourcemap: mode === 'production' ? false : true,

      rollupOptions: {
        input: {
          main: resolve(INPUT_DIR, 'main.js'),
        },
        output: {
          chunkFileNames: undefined,
          /*manualChunks(id) {
            if (id.includes('node_modules')) {
              return id.toString().split('node_modules/')[1].split('/')[0].toString();
            }
          },

          manualChunks: {
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

