import { createApp } from 'vue'
import App from '~@/App.vue'
import pinia from '~@/core/pinia'
import { criarRouter } from '~@/core/router'
import { iniciarShell } from '~@/core/shell'
import { abrirElemento, iniciarGatilhos } from '~@/core/triggers'
import { toastsDasMensagens } from '~@/overlays/mensagens'
import { useAuthStore } from '~@/stores/AuthStore'
import { useGlobalStore } from '~@/stores/GlobalStore'
import EventBus from '~@/utils/EventBus'

// Boot do v8: um app Vue e um Pinia por página (V8-ARQ-030). Chamar de novo devolve o mesmo.

export const ID_DO_APP = 'cmj-v8-app'
const ID_DO_MENU = 'v8-menu-principal'

let inicio = null

// Em tela estreita o menu do servidor abre como drawer, pela mesma pilha (V8-SHELL-032 e 034).
function abrirMenuEstreito(botao) {
  abrirElemento(ID_DO_MENU, { side: 'left', size: 'sm', title: 'Menu' }, botao)
}

async function montar() {
  const alvo = document.getElementById(ID_DO_APP)
  if (!alvo) {
    return null
  }
  const global = useGlobalStore(pinia)
  global.carregar()
  useAuthStore(pinia).hidratar()

  const router = await criarRouter(global)
  const app = createApp(App)
  // EventBus para comunicação entre componentes, como no v6.
  app.provide('EventBus', EventBus)
  app.config.globalProperties.$EventBus = EventBus
  app.use(pinia).use(router)
  app.mount(alvo)
  await router.isReady()

  iniciarShell({ abrirMenuEstreito })
  iniciarGatilhos()
  toastsDasMensagens()
  return app
}

export function iniciar() {
  if (!inicio) {
    inicio = montar()
  }
  return inicio
}
