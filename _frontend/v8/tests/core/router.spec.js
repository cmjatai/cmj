import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { defineComponent, h } from 'vue'
import { createMemoryHistory, RouterLink, RouterView } from 'vue-router'
import pinia from '~@/core/pinia'
import { criarRouter, nomeDaRotaDaZona } from '~@/core/router'
import ZoneOutlet from '~@/core/ZoneOutlet.vue'
import DrawerRota from '~@/overlays/DrawerRota.vue'
import OverlayHost from '~@/overlays/OverlayHost.vue'
import { useOverlayStore } from '~@/overlays/OverlayStore'
import { useOverlay } from '~@/overlays/useOverlay'
import { useGlobalStore } from '~@/stores/GlobalStore'
import navegacao from '~@/core/navegacao'

vi.mock('~@/core/navegacao', () => {
  const api = { ir: vi.fn(), recarregar: vi.fn(), abrirNovaAba: vi.fn(), caminhoAtual: () => '/' }
  return { ...api, default: api }
})

const PREFIXO = '/v8/demo/spa'
let montado
let store
const controles = {}

async function assentar() {
  for (let i = 0; i < 4; i += 1) {
    await flushPromises()
    await new Promise(resolver => setTimeout(resolver, 0))
  }
}

const Lista = defineComponent({
  render: () => h('div', { 'data-lista': '' }, [
    h(RouterLink, { to: { name: 'cliente', params: { id: 7 } }, 'data-link': '' }, () => 'Ana'),
    h(DrawerRota)
  ])
})
const Cliente = defineComponent({
  props: { id: { type: String, default: '' } },
  setup(props) {
    controles.cliente = useOverlay()
    return () => h('div', { 'data-cliente': props.id }, [h(DrawerRota)])
  }
})
const Pedido = defineComponent({ render: () => h('div', { 'data-pedido': '' }, 'pedido') })

function zonaDeTeste() {
  return {
    layout: defineComponent({ render: () => h('section', { 'data-layout-zona': '' }, [h(RouterView)]) }),
    rotas: [
      { path: '', name: 'inicio', redirect: { name: 'lista' } },
      {
        path: 'clientes',
        name: 'lista',
        component: Lista,
        meta: { breadcrumb: 'Clientes' },
        children: [{
          path: ':id(\\d+)',
          name: 'cliente',
          component: Cliente,
          props: true,
          meta: { breadcrumb: 'Cliente', drawer: { side: 'right', size: 'lg', title: 'Cliente' } },
          children: [{
            path: 'pedidos/:pedido(\\d+)',
            name: 'pedido',
            component: Pedido,
            meta: { drawer: { side: 'right', size: 'sm', title: 'Pedido' } }
          }]
        }]
      }
    ]
  }
}

async function iniciarZona(caminho, { zona = 'demo-spa', carregar } = {}) {
  document.body.innerHTML = `
    <nav><ol data-v8-trilha><li><a href="/v8/">Início</a></li><li aria-current="page">Demonstração SPA</li></ol></nav>
    <div data-vue-zone="demo-spa"><p data-espera>Carregando…</p></div>`
  const global = useGlobalStore(pinia)
  global.$patch({ zona, zonas: { 'demo-spa': PREFIXO } })
  const registroDeZonas = { 'demo-spa': carregar || vi.fn(() => Promise.resolve({ default: zonaDeTeste() })) }
  const router = await criarRouter(global, { historico: createMemoryHistory(), registroDeZonas, registroDePaineis: {} })
  router.push(caminho)
  await router.isReady()
  montado = mount(defineComponent({ render: () => [h(ZoneOutlet), h(OverlayHost)] }), {
    attachTo: document.body,
    global: { plugins: [pinia, router] }
  })
  await assentar()
  return { router, registroDeZonas }
}

beforeEach(() => {
  store = useOverlayStore(pinia)
  store.$limpar()
  navegacao.ir.mockClear()
})

afterEach(() => {
  montado?.unmount()
  montado = null
  store.$limpar()
  useGlobalStore(pinia).$patch({ zona: null, zonas: {} })
})

describe('zona SPA', () => {
  it('V8-ARQ-037: registra as rotas da zona sob o prefixo e desenha em [data-vue-zone]', async () => {
    const { router, registroDeZonas } = await iniciarZona(`${PREFIXO}/`)
    expect(registroDeZonas['demo-spa']).toHaveBeenCalledTimes(1)
    expect(router.hasRoute(nomeDaRotaDaZona('demo-spa'))).toBe(true)
    expect(router.currentRoute.value.name).toBe('lista')
    const zona = document.querySelector('[data-vue-zone]')
    expect(zona.querySelector('[data-layout-zona] [data-lista]')).not.toBeNull()
    expect(zona.querySelector('[data-espera]')).toBeNull()
  })

  it('V8-ARQ-037: em página sem zona, nenhum módulo de zona é importado', async () => {
    const carregar = vi.fn(() => Promise.resolve({ default: zonaDeTeste() }))
    const { router } = await iniciarZona('/v8/demo/clientes/', { zona: null, carregar })
    expect(carregar).not.toHaveBeenCalled()
    expect(router.hasRoute(nomeDaRotaDaZona('demo-spa'))).toBe(false)
    expect(document.querySelector('[data-espera]')).not.toBeNull()
  })

  it('V8-ARQ-038: dentro da zona navega sem recarregar; para fora é carga de página', async () => {
    const { router } = await iniciarZona(`${PREFIXO}/clientes`)
    await router.push(`${PREFIXO}/clientes/7`)
    await assentar()
    expect(navegacao.ir).not.toHaveBeenCalled()
    expect(router.currentRoute.value.name).toBe('cliente')

    await router.push('/v8/demo/clientes/?q=ana')
    await assentar()
    expect(navegacao.ir).toHaveBeenCalledWith('/v8/demo/clientes/?q=ana')
    expect(router.currentRoute.value.name).toBe('cliente')
  })

  it('V8-ARQ-038: em página sem zona, o router só altera a query string', async () => {
    const { router } = await iniciarZona('/v8/demo/clientes/', { zona: null })
    await router.push({ path: '/v8/demo/clientes/', query: { q: 'ana' } })
    expect(navegacao.ir).not.toHaveBeenCalled()
    expect(router.currentRoute.value.query).toEqual({ q: 'ana' })
    await router.push('/v8/outra/')
    expect(navegacao.ir).toHaveBeenCalledWith('/v8/outra/')
    expect(router.currentRoute.value.path).toBe('/v8/demo/clientes/')
  })

  it('V8-ARQ-039: caminho desconhecido dentro da zona mostra o 404 no miolo', async () => {
    const { router } = await iniciarZona(`${PREFIXO}/nao/existe`)
    await assentar()
    expect(router.currentRoute.value.name).toBe(`${nomeDaRotaDaZona('demo-spa')}_404`)
    const zona = document.querySelector('[data-vue-zone]')
    expect(zona.querySelector('[data-layout-zona]')).not.toBeNull()
    expect(zona.textContent).toContain('Página não encontrada')
    expect(navegacao.ir).not.toHaveBeenCalled()
  })

  it('V8-ARQ-064: zona fora do registro não importa nada e mantém o HTML do servidor', async () => {
    const carregar = vi.fn()
    const { router } = await iniciarZona(`${PREFIXO}/`, { zona: 'constructor', carregar })
    expect(carregar).not.toHaveBeenCalled()
    expect(router.getRoutes()).toHaveLength(1)
    expect(document.querySelector('[data-espera]')).not.toBeNull()
  })

  it('V8-SHELL-022: a rota acrescenta seus níveis à trilha do servidor', async () => {
    const { router } = await iniciarZona(`${PREFIXO}/clientes/7`)
    const itens = () => [...document.querySelectorAll('[data-v8-trilha] li')]
    expect(itens().map(li => li.textContent.trim())).toEqual(['Início', 'Demonstração SPA', 'Clientes', 'Cliente'])
    expect(itens().filter(li => li.getAttribute('aria-current') === 'page').map(li => li.textContent.trim()))
      .toEqual(['Cliente'])
    expect(itens()[2].querySelector('a').getAttribute('href')).toBe(`${PREFIXO}/clientes`)

    await router.push(`${PREFIXO}/clientes`)
    await assentar()
    expect(itens().map(li => li.textContent.trim())).toEqual(['Início', 'Demonstração SPA', 'Clientes'])
  })
})

describe('drawer por rota aninhada', () => {
  function drawers() {
    return [...document.querySelectorAll('[data-overlay-id]')]
  }

  it('V8-OVL-053: a rota filha aparece num drawer com as opções de meta.drawer', async () => {
    await iniciarZona(`${PREFIXO}/clientes/7`)
    const [drawer] = drawers()
    expect(drawer.getAttribute('role')).toBe('dialog')
    expect(drawer.classList.contains('v8-drawer-right')).toBe(true)
    expect(drawer.classList.contains('v8-tamanho-lg')).toBe(true)
    expect(drawer.querySelector('[data-cliente="7"]')).not.toBeNull()
    // A lista continua desenhada por baixo.
    expect(document.querySelector('[data-vue-zone] [data-lista]')).not.toBeNull()
    expect(store.pilha.map(e => e.source)).toEqual(['rota'])
  })

  it('V8-OVL-053: rota filha de rota filha empilha, e fechar leva à rota pai', async () => {
    const { router } = await iniciarZona(`${PREFIXO}/clientes/7/pedidos/3`)
    expect(drawers()).toHaveLength(2)
    expect(store.pilha).toHaveLength(2)
    expect(drawers()[1].querySelector('[data-pedido]')).not.toBeNull()

    drawers()[1].querySelector('[data-overlay-fechar]').click()
    await assentar()
    expect(router.currentRoute.value.fullPath).toBe(`${PREFIXO}/clientes/7`)
    expect(drawers()).toHaveLength(1)

    drawers()[0].querySelector('[data-overlay-fechar]').click()
    await assentar()
    expect(router.currentRoute.value.fullPath).toBe(`${PREFIXO}/clientes`)
    expect(drawers()).toHaveLength(0)
    expect(store.pilha).toHaveLength(0)
  })

  it('V8-OVL-053: o botão voltar fecha o drawer da rota', async () => {
    const { router } = await iniciarZona(`${PREFIXO}/clientes`)
    document.querySelector('[data-link]').click()
    await assentar()
    expect(router.currentRoute.value.name).toBe('cliente')
    expect(drawers()).toHaveLength(1)
    router.back()
    await assentar()
    expect(router.currentRoute.value.name).toBe('lista')
    expect(drawers()).toHaveLength(0)
  })

  it('V8-OVL-054: drawer de rota e drawer do store usam a mesma pilha', async () => {
    await iniciarZona(`${PREFIXO}/clientes/7`)
    store.openDrawer({ componente: Pedido }, { title: 'Local' })
    await assentar()
    expect(store.pilha.map(e => e.source)).toEqual(['rota', 'local'])
    expect(drawers()).toHaveLength(2)
    expect(drawers()[1].hasAttribute('data-overlay-topo')).toBe(true)
    expect(drawers()[0].hasAttribute('data-overlay-topo')).toBe(false)
    expect(drawers()[0].style.getPropertyValue('--v8-profundidade')).toBe('1')
  })

  it('V8-OVL-024: com alteração no drawer da rota, sair dela pede confirmação', async () => {
    const { router } = await iniciarZona(`${PREFIXO}/clientes/7`)
    controles.cliente.setDirty(true)
    router.push(`${PREFIXO}/clientes`)
    await assentar()
    expect(store.topo.type).toBe('confirm')
    document.querySelector('[data-confirm-botao=cancelar]').click()
    await assentar()
    expect(router.currentRoute.value.fullPath).toBe(`${PREFIXO}/clientes/7`)
    expect(drawers()).toHaveLength(1)
  })
})
