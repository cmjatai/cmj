import { createApp as _createApp, createSSRApp, defineComponent, h, reactive } from 'vue'
import { setPageContext } from './usePageContext'
import { createRouter } from './router'
import type { Component, PageContext } from './types'
import App from './App.vue'
import { createStore } from './stores'

export { createApp }
const isSSR = typeof window === 'undefined';

function createApp(pageContext: PageContext) {

  const PageWithShareContext = defineComponent({
    components: { App },
    render: () => h(App)
  })

  const app = isSSR ? createSSRApp(PageWithShareContext) : createSSRApp(PageWithShareContext)

  const pageContextReactive = reactive(pageContext)

  setPageContext(app, pageContextReactive,  (title:string) => {
    pageContext.documentProps.title = title
    
    if ( !import.meta.env.SSR ) {
      document.title = title
    }
  })
  
  const router = createRouter()
  const store = createStore()

  app.use(router)
  app.use(store)

  return { app, router, store }
}
