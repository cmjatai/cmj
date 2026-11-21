// Apoio aos testes da demonstração: dados de exemplo, overlay de mentira, router da zona e
// leitura dos stores de overlays e de toasts.
import { vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import pinia from '~@/core/pinia'
import { useOverlayStore } from '~@/overlays/OverlayStore'
import { useToastStore } from '~@/overlays/ToastStore'
import { CHAVE_OVERLAY } from '~@/overlays/useOverlay'
import zona from '~@/modules/demo/zona'

export const PREFIXO = '/v8/demo/spa'

export function clienteDeExemplo(extra = {}) {
  return {
    id: 7,
    nome: 'Glória Exemplo',
    email: 'gloria.exemplo@exemplo.invalid',
    cidade: 'Jataí',
    situacao: 'ativo',
    motivo: '',
    desde: '2021-09-07',
    pedidos: [
      { id: 701, descricao: 'Caderno de anotações', valor: '19.90', data: '2021-10-07' },
      { id: 702, descricao: 'Caixa de canetas', valor: '138.55', data: '2021-11-06' }
    ],
    ...extra
  }
}

export function paginaDeExemplo(extra = {}) {
  const itens = [
    { id: 1, nome: 'Ana Exemplo', email: 'ana.exemplo@exemplo.invalid', cidade: 'Caiapônia', situacao: 'ativo', motivo: '', desde: '2021-01-04', total_pedidos: 1 },
    { id: 4, nome: 'Davi Exemplo', email: 'davi.exemplo@exemplo.invalid', cidade: 'Jataí', situacao: 'inativo', motivo: 'Cadastro duplicado', desde: '2021-05-07', total_pedidos: 4 }
  ]
  return { total: 2, pagina: 1, paginas: 1, tamanho: 10, itens, ...extra }
}

// O que useOverlay() devolve dentro de um drawer ou modal. Com `rodapeEl: null`, o
// OverlayFooter desenha as ações no próprio lugar.
export function overlayDeMentira(extra = {}) {
  return {
    id: 'overlay-de-teste',
    rodapeEl: null,
    close: vi.fn(),
    dismiss: vi.fn(),
    setDirty: vi.fn(),
    setTitle: vi.fn(),
    ...extra
  }
}

export function comOverlay(overlay) {
  return { [CHAVE_OVERLAY]: overlay }
}

// As rotas da zona entram como filhas do prefixo, do mesmo modo que em src/core/router.js.
export function criarRouterDaZona() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      {
        path: PREFIXO,
        name: 'v8_zona_demo-spa',
        component: zona.layout,
        children: [...zona.rotas]
      }
    ]
  })
}

export function overlaysAbertos() {
  const store = useOverlayStore(pinia)
  return store.entradas.map(entrada => ({ ...entrada, conteudo: store.conteudo(entrada.id) }))
}

export function fecharOverlay(id, valor) {
  useOverlayStore(pinia).close(id, valor)
}

export function toasts() {
  return useToastStore(pinia).visiveis.map(toast => ({ nivel: toast.nivel, texto: toast.texto }))
}

export function limparStores() {
  useOverlayStore(pinia).$limpar()
  useToastStore(pinia).limpar()
}

// Deixa terminarem as promessas pendentes e os import() sob demanda.
export async function assentar() {
  await flushPromises()
  await vi.dynamicImportSettled()
  await flushPromises()
}
