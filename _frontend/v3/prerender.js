// Pre-render the app into static HTML.
// run `npm run generate` and then `dist/static` can be served as a static site.

import { readFileSync, readdirSync, writeFileSync, unlinkSync } from 'fs'
import { resolve } from 'path'

const toAbsolute = (p) => resolve(__dirname, p)

import manifest from './dist/static/ssr-manifest.json'
const template = readFileSync(toAbsolute('dist/static/index.html'), 'utf-8')
import { render } from './dist/server/entry-server.js'

// determine routes to pre-render from src/pages
const routesToPrerender = readdirSync(toAbsolute('src/pages')).map((file) => {
  const name = file.replace(/\.vue$/, '').toLowerCase()
  return name === 'home' ? `/` : `/${name}`
})

;(async () => {
  // pre-render each route...
  for (const url of routesToPrerender) {
    const [appHtml, preloadLinks] = await render(url, manifest)

    const html = template
      .replace(`<!--preload-links-->`, preloadLinks)
      .replace(`<!--app-html-->`, appHtml)

    const filePath = `dist/static${url === '/' ? '/index' : url}.html`
    writeFileSync(toAbsolute(filePath), html)
    console.log('pre-rendered:', filePath)
  }

  // done, delete ssr manifest
  unlinkSync(toAbsolute('dist/static/ssr-manifest.json'))
})()
