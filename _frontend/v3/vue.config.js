const path = require('path')
const each = require('lodash/fp/each')

const shell = require('shelljs')

const BundleTrackerPlugin = require('webpack-bundle-tracker')

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
  path: '../../cmj3/.env'
})

const HOST_NAME = 'localhost'

module.exports = {
  runtimeCompiler: true,
  publicPath: process.env.NODE_ENV === 'production' ? '/static' : `http://${HOST_NAME}:8080/`,

  chainWebpack: config => {
    config
      .plugin('RelativeBundleTrackerPlugin')
      .use(RelativeBundleTrackerPlugin, [{
        path: '.',
        filename: `./${process.env.DEBUG === 'True' && process.env.NODE_ENV !== 'production' ? 'dev-' : ''}webpack-stats.json`
      }])

    if (process.env.NODE_ENV === 'production') {
      shell
        .rm('./dev-webpack-stats.json')
    }
  }
}
