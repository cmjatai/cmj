const path = require('path')
const each = require('lodash/fp/each')

const shell = require('shelljs')

const BundleTrackerPlugin = require('webpack-bundle-tracker')
const CompressionPlugin = require('compression-webpack-plugin')
const TerserPlugin = require('terser-webpack-plugin')
const CopyPlugin = require('copy-webpack-plugin')
const { InjectManifest } = require('workbox-webpack-plugin')

const dotenv = require('dotenv')
dotenv.config({
  path: '../../cmj/.env'
})

let HOST_NAME = 'localhost'
HOST_NAME = '192.168.15.9'
// HOST_NAME = '10.42.0.1'
// HOST_NAME = '10.3.163.21'
// HOST_NAME = '10.3.162.151'
// HOST_NAME = '168.228.184.70'
let BACKENDPORT = '9098'
BACKENDPORT = '9099'
// PORT = '8080'

module.exports = {
  runtimeCompiler: true,
  publicPath: process.env.NODE_ENV === 'production' ? '/static/v2018' : `http://${HOST_NAME}:8080/`,
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

    config.plugin('provide')
      .use(require('webpack').ProvidePlugin, [{
        $: 'jquery',
        jQuery: 'jquery',
        'window.jQuery': 'jquery',
        '_': 'lodash'
      }])

    config.plugin('BundleTrackerPlugin')
      .use(BundleTrackerPlugin, [{
        path: '.',
        relativePath: true,
        filename: `${process.env.DEBUG === 'True' && process.env.NODE_ENV !== 'production' ? 'dev-' : ''}webpack-stats.json`
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
      config.devtool('inline-source-map')

      config.plugin('workbox')
        .use(InjectManifest, [{
          swSrc: path.resolve(__dirname, 'src/service-worker.js'),
          swDest: 'service-worker-dev.js',
          exclude: [/\.map$/]
        }])
    }

    if (process.env.NODE_ENV === 'production') {
      config.devtool(false)
      shell.rm('./dev-webpack-stats.json')

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
    }

  },

  pwa: {
    name: 'PortalCMJ',
    themeColor: '#114d81',
    msTileColor: '#114d81',
    appleMobileWebAppCapable: 'yes',
    appleMobileWebAppStatusBarStyle: 'black',
    manifestOptions: {
      id: 'br.leg.go.jatai.portalcmj.v2018',
      start_url: process.env.NODE_ENV === 'production' ? '/' : `http://${HOST_NAME}:${BACKENDPORT}/`,
      theme_color: '#114d81',
      background_color: '#ffffff'
    },
    iconPaths: {
      favicon32: 'img/icons/favicon-32x32.png',
      favicon16: 'img/icons/favicon-16x16.png',
      appleTouchIcon: 'img/icons/apple-touch-icon-152x152.png',
      msTileImage: 'img/icons/mstile-150x150.png',
      androidChromeIcon: 'img/icons/android-chrome-192x192.png',
      androidChromeIcon512: 'img/icons/android-chrome-512x512.png'
    },
    workboxPluginMode: 'InjectManifest',
    workboxOptions: {
      swSrc: path.join(__dirname, 'src', 'service-worker.js'),
      maximumFileSizeToCacheInBytes: 5 * 1024 * 1024 // 5 MB
    }
  }
}
