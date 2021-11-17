import express from 'express'
import * as vite from 'vite'
import fs from 'fs'
import path from 'path'

const isProduction = process.env.NODE_ENV === 'production'
const root = `${__dirname}/..`

startServer()

async function startServer() {
  const app = express()


  const indexProd = isProduction
    ? fs.readFileSync(
      path.resolve(root, 'dist/client/index.html'),
      'utf-8'
    ) : ''
      
  const ssrMmanifest = isProduction ? JSON.parse(fs.readFileSync(path.resolve(root, 'dist/client/ssr-manifest.json'), 'utf-8')) : {}

  let viteDevServer: any
  if (isProduction) {
    app.use(express.static(`${root}/dist/client`, {index: false}))
  } else {
    viteDevServer = await vite.createServer({
      root,
      server: { middlewareMode: 'ssr' }
    })
    app.use(viteDevServer.middlewares)
  }

  app.get('*', async (req, res, next) => {
    const url = req.originalUrl
    console.log(url)

    try {

      let template: any
      let render: any

      if (!isProduction) {
        // always read fresh template in dev
        template = fs.readFileSync(path.resolve(root, 'index.html'), 'utf-8')
        template = await viteDevServer.transformIndexHtml(url, template)

        render = await viteDevServer.ssrLoadModule('/src/entry-server.ts')
        render = render.render
      } else {
        template = indexProd
        render = require('../dist/server/entry-server.js')
        render = render.render
      }

      const rendered = await render(url, ssrMmanifest, __dirname)
      
      const repls = [ 
        { // subset
          '<!--head-links-->': [  //mask: [rendereds]
            {rendered:rendered.favicons, reIncludeMask: true},
            {rendered:rendered.preloadLinks, reIncludeMask: false}
          ]
        },
        {
          '<!--ssr-outlet-->': [
            {rendered:rendered.appHtml, reIncludeMask: false}
          ],
        }
      ]

      let html = template

      repls.forEach((subset: any) => {
        Object.keys(subset).map((mask: string) => {
          subset[mask].forEach((value:any) => {

            const reIncludeMask = value.reIncludeMask ? mask : ''
            html = html.replace(mask, `${value.rendered}${reIncludeMask}`)  
            
            // console.log(value, mask, reIncludeMask,  html)        
          })
        })
      })
      // html = html.split('><').join('>\n<')
      // html = html.split('> <').join('>\n<')      
      // console.log(repls, html)

      res.status(200).set({ 'Content-Type': 'text/html' }).end(html) //

    } catch (e: any) {
      if (!isProduction) {
        viteDevServer.ssrFixStacktrace(e)
      }
      console.error(e)
      res.status(500).end(e.message)
    }
  })

  const port = 3000
  app.listen(port)
  console.log(`Server running at http://localhost:${port}`)
}
