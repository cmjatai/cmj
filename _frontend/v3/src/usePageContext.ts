// Hook `usePageContext()` to make `pageContext` available from any Vue component.
// See https://vite-plugin-ssr.com/pageContext-anywhere

import { inject } from 'vue'
import { PageContext } from './types'

export { usePageContext }
export { setPageContext }

const keyObject = Symbol()
const keyUpdateObject = Symbol()

function usePageContext() {
  const pageContext = inject(keyObject)
  const updateTitle = inject(keyUpdateObject)
  return { pageContext , updateTitle }
}


function setPageContext(app: any, pageContext: PageContext, updateTitle: Function) {
  app.provide(keyObject, pageContext)
  app.provide(keyUpdateObject, updateTitle)
}
