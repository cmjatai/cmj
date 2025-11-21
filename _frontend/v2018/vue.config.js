const path = require('path')
const each = require('lodash/fp/each')

const shell = require('shelljs')

const BundleTrackerPlugin = require('webpack-bundle-tracker')
const CompressionPlugin = require('compression-webpack-plugin')
const MomentLocalesPlugin = require('moment-locales-webpack-plugin')
const TerserPlugin = require('terser-webpack-plugin')
const CopyPlugin = require('copy-webpack-plugin')

class RelativeBundleTrackerPlugin extends BundleTrackerPlugin {
  convertPathChunks (chunks) {
    each(each(chunk => {
      chunk.path = path.relative(this.options.path, chunk.path)
    }))(chunks)
  }
  writeOutput (compiler, contents) {
    if (contents.status === 'done') {
      this.convertPathChunks(contents.chunks)
    }
    super.writeOutput(compiler, contents)
  }
}


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
let PORT = '9098'
PORT = '9099'
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

    config.plugin('provide')
      .use(require('webpack').ProvidePlugin, [{
        $: 'jquery',
        jQuery: 'jquery',
        'window.jQuery': 'jquery',
        '_': 'lodash'
      }])

    if (process.env.NODE_ENV !== 'production') {
      const { InjectManifest } = require('workbox-webpack-plugin')
      config.plugin('workbox')
        .use(InjectManifest, [{
          swSrc: path.resolve(__dirname, 'src/service-worker.js'),
          swDest: 'service-worker-dev.js',
          exclude: [/\.map$/]
        }])
    }

    config.plugin('BundleTrackerPlugin')
      .use(BundleTrackerPlugin, [{
        path: '.',
        relativePath: true,
        filename: `${process.env.DEBUG === 'True' && process.env.NODE_ENV !== 'production' ? 'dev-' : ''}webpack-stats.json`
      }])

    config.plugin('copy').use(CopyPlugin, [
      {
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
      }
    ])

    config.plugin('MomentLocalesPlugin').use(MomentLocalesPlugin, [
      {
        localesToKeep: ['pt-BR']
      }
    ])

    if (process.env.NODE_ENV === 'production') {
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

      shell
        .rm('./dev-webpack-stats.json')
    } else {
      config.devtool('inline-source-map')
    }

    /* config.module
      .rule('worker')
      .test(/\.worker\.js$/)
      .use('worker-loader')
        .loader('worker-loader')
        .options({
          inline: 'fallback'
        })
        .end() */

    /* config.module
      .rule('js')
      .exclude
        .add(/\.worker\.js$/) */

    config.module
      .rule('vue')
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

    config.entry('construct')
      .add('./src/__construct/main.js')
      .end()

    config.entry('compilacao')
      .add('./src/__apps/compilacao/main.js')
      .end()

      config.entry('painel')
      .add('./src/__apps/painel/main.js')
      .end()

      config.entry('loa')
      .add('./src/__apps/loa/main.js')
      .end()


    /*
    config.entryPoints.delete('app')
     config.entry('app')
      .add('./src/main.js')
      .end()  */
  },
  pwa: {
    name: 'PortalCMJ-Frontend-v2018',
    themeColor: '#114d81',
    msTileColor: '#114d81',
    appleMobileWebAppCapable: 'yes',
    appleMobileWebAppStatusBarStyle: 'black',
    manifestOptions: {
      id: 'br.leg.go.jatai.portalcmj',
      start_url: process.env.NODE_ENV === 'production' ? '/' : `http://${HOST_NAME}:${PORT}/`,
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
