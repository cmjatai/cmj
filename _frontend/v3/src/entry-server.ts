import { createApp } from './main'
import { renderToString, SSRContext} from 'vue/server-renderer'

export async function render(url:string, ssrMmanifest: object, rootDir: string) {
  const { app, router } = createApp()

  router.push(url)
  await router.isReady()

  const ctx: SSRContext = {}
  let html = await renderToString(app, ctx)
  
  const preloadLinks = renderPreloadLinks(ctx.modules, ssrMmanifest)
  return [html, preloadLinks]
}

function renderPreloadLinks(modules:any, ssrMmanifest:object) {
  // console.log(ssrMmanifest)
  let links = ''
  const seen = new Set()
  modules.forEach((id:string) => {
    const files:[] = ssrMmanifest[id]
    if (files) {
      files.forEach((file:string) => {
        if (!seen.has(file)) {
          seen.add(file)
          links += renderPreloadLink(file)
        }
      })
    }
  })
  return links
}

function renderPreloadLink(file: string) {
  if (file.endsWith('.js')) {
    return `<link rel="modulepreload" crossorigin href="${file}">`
  } else if (file.endsWith('.css')) {
    return `<link rel="stylesheet" href="${file}">`
  } else if (file.endsWith('.woff')) {
    return ` <link rel="preload" href="${file}" as="font" type="font/woff" crossorigin>`
  } else if (file.endsWith('.woff2')) {
    return ` <link rel="preload" href="${file}" as="font" type="font/woff2" crossorigin>`
  } else if (file.endsWith('.gif')) {
    return ` <link rel="preload" href="${file}" as="image" type="image/gif">`
  } else if (file.endsWith('.jpg') || file.endsWith('.jpeg')) {
    return ` <link rel="preload" href="${file}" as="image" type="image/jpeg">`
  } else if (file.endsWith('.png')) {
    return ` <link rel="preload" href="${file}" as="image" type="image/png">`
  } else {
    // TODO
    return ''
  }
}
