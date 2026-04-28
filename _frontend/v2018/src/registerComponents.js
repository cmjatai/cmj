import Vue from 'vue'
import App from './App'
import AppPntp from './modules/pntp/AppPntp.vue'
import AppMenuPntp from './modules/pntp/AppMenuPntp.vue'
import AppListPntp from './modules/pntp/AppListPntp.vue'
import AppDoclistPntp from './modules/pntp/AppDoclistPntp.vue'
import PntpMenuItem from './modules/pntp/PntpMenuItem.vue'
import PntpListItem from './modules/pntp/PntpListItem.vue'
import PntpDoclistItem from './modules/pntp/PntpDoclistItem.vue'

Vue.component('App', App)
Vue.component('AppPntp', AppPntp)
Vue.component('AppMenuPntp', AppMenuPntp)
Vue.component('AppListPntp', AppListPntp)
Vue.component('AppDoclistPntp', AppDoclistPntp)
Vue.component('PntpMenuItem', PntpMenuItem)
Vue.component('PntpListItem', PntpListItem)
Vue.component('PntpDoclistItem', PntpDoclistItem)
