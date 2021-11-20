import { createSSRApp, defineComponent, h, reactive } from 'vue'
import { setPageContext } from './usePageContext'
import { createRouter } from './router'
import type { Component, PageContext } from './types'
import App from './App.vue'
import Api from './plugins/api'

export { createApp }

function createApp(pageContext: PageContext) {

  let rootComponent: Component
  const PageWithShareContext = defineComponent({
    data: () => ({}),
    created() {
      rootComponent = this
    },
    render() {
      return h(App)      
    }
  })

  const app = createSSRApp(PageWithShareContext)

  const pageContextReactive = reactive(pageContext)

  setPageContext(app, pageContextReactive,  (title:string) => {
    pageContext.documentProps.title = title
    
    if ( !import.meta.env.SSR ) {
      document.title = title
    }
  })
  
  const router = createRouter()
  app.use(router)
  app.use(Api)
  return { app, router }
}
