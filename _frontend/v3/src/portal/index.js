import { createApp } from 'vue'
import BodyBaseDjangoTemplate from './root/BodyBaseDjangoTemplate'
import router from './router'
import store from './store'

import mixins from './mixins'

const portal = createApp({
  delimiters: ['[[', ']]'],
  extends: {
    ...BodyBaseDjangoTemplate
  }
}).use(store).use(router)

portal.mixin(mixins)

portal.mount('#app-vue')

export default portal
