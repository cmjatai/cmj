const path = require('path')
const each = require('lodash/fp/each')

const shell = require('shelljs')

const BundleTrackerPlugin = require('webpack-bundle-tracker')
const CompressionPlugin = require('compression-webpack-plugin')
const CopyPlugin = require('copy-webpack-plugin')
const WebpackPwaManifest = require('webpack-pwa-manifest')
const WorkboxPlugin = require('workbox-webpack-plugin')

const dotenv = require('dotenv')
dotenv.config({
   path: '../../cmj/.env'
})

let DEV_HOST_NAME = process.env.DEV_HOST_NAME || 'localhost'
let DEV_BACKENDPORT = process.env.DEV_BACKENDPORT || '8000'

module.exports = {
  runtimeCompiler: true,
  publicPath: process.env.NODE_ENV === 'production' ? '/static/v2018' : `http://${DEV_HOST_NAME}:8080/`,
  outputDir: 'dist/v2018',
  devServer: {
    headers: {
      'Access-Control-Allow-Origin': '*'
    },
    hot: true,
    https: false,
    port: 8080,
    host: '0.0.0.0',
    allowedHosts: 'all',
    static: {
      directory: path.join(__dirname, 'src', 'assets'),
      publicPath: '',
      watch: true
    }
  },

  chainWebpack: config => {

    config.entry('construct')
      .add('./src/__construct/main.js')
      .end()

    config.entry('compilacao')
      .add('./src/__apps/compilacao/main.js')
      .end()

    config.entry('loa')
      .add('./src/__apps/loa/main.js')
      .end()

    config.entry('libsuserauth')
      .add('./src/__apps/libsuserauth/main.js')
      .end()

    config.plugin('provide')
      .use(require('webpack').ProvidePlugin, [{
        $: 'jquery',
        jQuery: 'jquery',
        'window.jQuery': 'jquery',
        //'window.$': 'jquery',
        '_': 'lodash'
      }])

    config.plugin('BundleTrackerPlugin')
      .use(BundleTrackerPlugin, [{
        path: '.',
        relativePath: true,
        filename: `${process.env.NODE_ENV !== 'production' ? 'dev-' : ''}webpack-stats.json`
      }])

    config.plugin('copy')
      .use(CopyPlugin, [{
        patterns: [
          {
            from: path.join(__dirname, '/node_modules/tinymce/skins'),
            to: 'js/skins/[path][name][ext]'
          },
          {
            from: path.join(__dirname, 'src', 'assets'),
            to: '[path][name][ext]'
          }
        ]
      }])

    config.module.rule('vue')
      .use('vue-loader')
      .loader('vue-loader')
      .tap(options => {
        options['transformAssetUrls'] = {
          img: 'src',
          image: 'xlink:href',
          'b-img': 'src',
          'b-img-lazy': ['src', 'blank-src'],
          'b-card': 'img-src',
          'b-card-img': 'img-src',
          'b-carousel-slide': 'img-src',
          'b-embed': 'src'
        }
        return options
      })

    if (process.env.NODE_ENV !== 'production') {
      config.devtool('eval-source-map')
    }

    if (process.env.NODE_ENV === 'production') {
      config.devtool(false)
      shell.rm('./dev-webpack-stats.json')

      config.optimization.splitChunks({
        chunks: 'all',
        maxInitialRequests: Infinity,
        minSize: 0,
        cacheGroups: {
          vendor: {
            test: /[\\/]node_modules[\\/]/,
            name(module) {
              const packageName = module.context.match(/[\\/]node_modules[\\/](.*?)([\\/]|$)/)
              if (!packageName) return 'npm.unknown'

              return `npm.${packageName[1].replace('@', '')}`
            }
          }
        }
      })

      config
        .optimization
        .minimizer('terser')
        .tap(args => {
          args[0]['terserOptions']['compress']['drop_console'] = true
          return args
        })

      config
        .plugin('CompressionPlugin')
        .use(CompressionPlugin, [{}])

      config.plugin('pwa-manifest')
        .use(WebpackPwaManifest, [{
          id: 'br.leg.go.jatai.portalcmj.v2018',
          name: 'PortalCMJ',
          short_name: 'PortalCMJ',
          description: 'Portal da Câmara Municipal de Jataí - GO',
          background_color: '#ffffff',
          theme_color: '#114d81',
          start_url: process.env.NODE_ENV === 'production' ? '/' : `http://${DEV_HOST_NAME}:${DEV_BACKENDPORT}/`,
          display: 'standalone',
          orientation: 'omit',
          fingerprints: false,
          inject: false,
          ios: {
            'apple-mobile-web-app-title': 'PortalCMJ',
            'apple-mobile-web-app-status-bar-style': 'black'
          },
          icons: [
            {
              src: path.resolve('src/assets/img/icons/android-chrome-192x192.png'),
              sizes: [192],
              destination: path.join('img', 'icons')
            },
            {
              src: path.resolve('src/assets/img/icons/android-chrome-512x512.png'),
              sizes: [512],
              destination: path.join('img', 'icons')
            }
          ]
        }])

      config.plugin('workbox')
        .use(WorkboxPlugin.InjectManifest, [{
          swSrc: path.resolve(__dirname, 'src/service-worker.js'),
          swDest: 'service-worker.js',
          exclude: [/\.map$/, /hot-update/, /manifest\.(json|js)$/],
          maximumFileSizeToCacheInBytes: 5 * 1024 * 1024
        }])
    }
  },
}
