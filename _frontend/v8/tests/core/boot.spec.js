import { describe, expect, it, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { getActivePinia } from 'pinia'
import pinia from '~@/core/pinia'
import { ID_DO_APP, iniciar } from '~@/core/boot'
import { useAuthStore } from '~@/stores/AuthStore'
import { useGlobalStore } from '~@/stores/GlobalStore'
import { useToastStore } from '~@/overlays/ToastStore'
import WebSocketManager from '~@/utils/ws/WebSocketManager'

vi.mock('~@/utils/ws/WebSocketManager', () => ({ default: vi.fn() }))

function script(id, dados) {
  const el = document.createElement('script')
  el.id = id
  el.type = 'application/json'
  el.textContent = JSON.stringify(dados)
  document.head.append(el)
}

describe('boot do v8', () => {
  it('V8-ARQ-030: um app e um Pinia por página, mesmo chamando o boot de novo', async () => {
    const pedidos = vi.fn()
    vi.stubGlobal('fetch', pedidos)
    script('v8-global', {
      autenticado: true,
      usuario: { id: 5, username: 'ana', nome: 'Ana Teste', avatar: null },
      permissoes: ['core.view_x'],
      zona: null,
      zonas: {}
    })
    script('v8-messages', [{ nivel: 'success', texto: 'Dois clientes arquivados.' }])
    document.body.innerHTML = `<main id="conteudo"><p id="servidor">{{ do servidor }}</p></main><div id="${ID_DO_APP}"></div>`

    const primeiro = iniciar()
    const segundo = iniciar()
    expect(segundo).toBe(primeiro)
    const app = await primeiro
    expect(await iniciar()).toBe(app)
    await flushPromises()

    expect(document.querySelectorAll('[data-v-app]')).toHaveLength(1)
    expect(document.getElementById(ID_DO_APP).hasAttribute('data-v-app')).toBe(true)
    expect(getActivePinia()).toBe(pinia)
    expect(app.config.globalProperties.$pinia).toBe(pinia)

    // V8-ARQ-031: o app fica no elemento próprio e não toca no HTML do servidor.
    expect(document.getElementById('servidor').textContent).toBe('{{ do servidor }}')

    // V8-ARQ-032: stores preenchidos pelo JSON da página, sem requisição.
    expect(useGlobalStore(pinia).usuario.nome).toBe('Ana Teste')
    const auth = useAuthStore(pinia)
    expect(auth.isAuthenticated).toBe(true)
    expect(auth.hasPermission('core.view_x')).toBe(true)
    expect(pedidos).not.toHaveBeenCalled()

    // V8-ARQ-041: nenhum WebSocket é aberto no boot.
    expect(WebSocketManager).not.toHaveBeenCalled()

    // V8-OVL-073: as mensagens do Django viram toasts.
    expect(useToastStore(pinia).visiveis.map(t => [t.nivel, t.texto]))
      .toEqual([['success', 'Dois clientes arquivados.']])
    expect(document.querySelector('.v8-toasts [role="status"]').textContent).toContain('Dois clientes arquivados.')
  })
})
