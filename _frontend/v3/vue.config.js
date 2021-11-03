const shell = require('shelljs')
const BundleTrackerPlugin = require('webpack-bundle-tracker')
const CompressionPlugin = require('compression-webpack-plugin')

const dotenv = require('dotenv')
dotenv.config({
  path: '../../cmj3/.env'
})

const HOST_NAME = 'localhost'

module.exports = {

  runtimeCompiler: true,
  publicPath: process.env.NODE_ENV === 'production' ? '/static' : `http://${HOST_NAME}:8080/`,
  productionSourceMap: false,

  chainWebpack: config => {
    config
      .plugin('html')
      .tap(options => {
        options[0].inject = false
        return options
      })

    config
      .plugin('BundleTrackerPlugin')
      .use(BundleTrackerPlugin, [{
        relativePath: true,
        filename: `./${process.env.DEBUG === 'True' && process.env.NODE_ENV !== 'production' ? 'dev-' : ''}webpack-stats.json`
      }])

    config
      .plugin('provide')
      .use(require('webpack/lib/ProvidePlugin'), [{
        // $: 'jquery',
        // jquery: 'jquery',
        // 'window.jQuery': 'jquery',
        // jQuery: 'jquery',
        _: 'lodash'
      }])

    if (process.env.NODE_ENV === 'production') {
      shell
        .rm('./dev-webpack-stats.json')

      const splitChunks = config.optimization.store.get('splitChunks')
      splitChunks.chunks = 'all'
      splitChunks.cacheGroups.defaultVendors.chunks = 'all'
      splitChunks.cacheGroups.common.chunks = 'all'
      config
        .optimization.splitChunks(splitChunks)

      config
        .plugin('CompressionPlugin')
        .use(CompressionPlugin, [])
    } else {
      config.devServer
        .headers({
          'Access-Control-Allow-Origin': '*'
        })
    }
  },

  pwa: {
    themeColor: '#4DBA87',
    msTileColor: '#000000',
    appleMobileWebAppCapable: 'yes',
    appleMobileWebAppStatusBarStyle: 'black',

    workboxPluginMode: 'InjectManifest',

    workboxOptions: {
      // swSrc is required in InjectManifest mode.
      swSrc: './public/service-worker.js'
      // ...other Workbox options...
    }
  }
}
