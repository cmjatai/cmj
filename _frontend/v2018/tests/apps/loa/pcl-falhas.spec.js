import { mount, shallowMount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import PclDetalheAjuste from '@/modules/loa/pcl/PclDetalheAjuste.vue'
import PclDetalheEmenda from '@/modules/loa/pcl/PclDetalheEmenda.vue'
import PrestacaoContaLoaLayout from '@/modules/loa/pcl/PrestacaoContaLoaLayout.vue'
import PclTabAjustes from '@/modules/loa/pcl/tabs/PclTabAjustes.vue'
import PclTabDocumentos from '@/modules/loa/pcl/tabs/PclTabDocumentos.vue'
import PclTabEmpenhos from '@/modules/loa/pcl/tabs/PclTabEmpenhos.vue'
import PclTabPrestacao from '@/modules/loa/pcl/tabs/PclTabPrestacao.vue'
import PclTabTramitacoes from '@/modules/loa/pcl/tabs/PclTabTramitacoes.vue'

import { esperar } from '../../apoio'

const metodos = PrestacaoContaLoaLayout.methods
const falha = (status) => Promise.reject(Object.assign(new Error('falha'), status ? { response: { status } } : {}))
const vazio = { data: { pagination: { total_entries: 0 }, results: [] } }
const OPCOES = { parlamentares: [{ id: 1, nome: 'Ana' }], unidades: [], entidades: [] }

const montarPainel = (fetch) => shallowMount(PrestacaoContaLoaLayout, {
  mocks: {
    $route: { params: { pkloa: 2026 }, query: {} },
    $router: { replace: vi.fn(() => Promise.resolve()) },
    utils: { fetch },
    removeAside: vi.fn()
  }
})
// backend que responde bem, salvo nos pedidos que `quebra` aponta
const backend = (quebra = () => null) => vi.fn((pedido) => {
  const status = quebra(pedido)
  if (status !== null) return falha(status)
  if (pedido.action === 'prestacaoconta_resumo') {
    return Promise.resolve({ data: { exercicios: [{ id: 2026, ano: 2026, selecionado: true }], itens: 0 } })
  }
  if (pedido.action === 'prestacaoconta_opcoes') return Promise.resolve({ data: OPCOES })
  if (pedido.action === 'prestacaoconta_itens') return Promise.resolve(vazio)
  return Promise.resolve({ data: { id: 2026, ano: 2026, parlamentares: [] } })
})

describe('falhas de requisição no painel', () => {
  it('LOA-PCL-104: falha na busca avisa na tela, em vez de "Nenhum resultado"', async () => {
    const wrapper = montarPainel(backend(p => (p.action === 'prestacaoconta_itens' ? 500 : null)))
    await esperar(10)

    expect(wrapper.vm.erro).toBe(true)
    expect(wrapper.find('.pcl-erro').text()).toContain('Não foi possível carregar os dados da prestação de contas.')
    expect(wrapper.text()).not.toContain('Nenhum resultado encontrado')
  })

  it('LOA-PCL-104: "Tentar novamente" refaz a busca e some quando ela dá certo', async () => {
    let quebrado = true
    const fetch = backend(p => (quebrado && p.action === 'prestacaoconta_resumo' && p.params ? 0 : null))
    const wrapper = montarPainel(fetch)
    await esperar(10)
    expect(wrapper.find('.pcl-erro').exists()).toBe(true)

    quebrado = false
    await wrapper.find('.pcl-erro button').trigger('click')
    await esperar(10)

    expect(wrapper.vm.erro).toBe(false)
    expect(wrapper.find('.pcl-erro').exists()).toBe(false)
    expect(wrapper.text()).toContain('Nenhum resultado encontrado')
  })

  it('LOA-PCL-104: 404 é LOA sem prestação de contas, não falha', async () => {
    const wrapper = montarPainel(backend(p => (p.action ? 404 : null)))
    await esperar(10)

    expect(wrapper.vm.erro).toBe(false)
    expect(wrapper.find('.pcl-erro').exists()).toBe(false)
    expect(wrapper.text()).toContain('Nenhum resultado encontrado')
  })

  it('LOA-PCL-104: falha na carga inicial mostra o aviso no lugar do painel em branco', async () => {
    let quebrado = true
    const wrapper = montarPainel(backend(p => (quebrado && !p.action ? 500 : null)))
    await esperar(10)

    expect(wrapper.find('.pcl-erro').exists()).toBe(true)
    expect(wrapper.vm.ready).toBe(false)

    quebrado = false
    await wrapper.find('.pcl-erro button').trigger('click')
    await esperar(10)
    expect([wrapper.vm.erro, wrapper.vm.ready]).toEqual([false, true])
  })

  it('LOA-PCL-104: falha no dashboard também avisa', async () => {
    const p = { _fetchId: 1, loa: { id: 2026 }, erro: false, dashboard: 'x', utils: { fetch: () => falha(500) }, getResumoParams: () => ({}), registrarFalha: metodos.registrarFalha }
    await metodos.fetchConsulta.call(p, 'dashboard', 1)

    expect([p.dashboard, p.erro]).toEqual([null, true])
  })
})

describe('falhas de requisição nas abas dos cartões', () => {
  beforeEach(() => {
    vi.stubGlobal('IntersectionObserver', class {
      observe () {}
      disconnect () {}
    })
  })
  afterEach(() => vi.unstubAllGlobals())

  const registroEmenda = () => ({
    __label__: 'loa_emendaloa',
    id: 11,
    tipo: 99,
    fase: 30,
    materia: { id: 900 },
    parlamentares: [],
    abas: { prestacao: 1, ajustes: 1, empenhos: 1, tramitacoes: 1, documentos: 0 }
  })
  const montar = (componente, registro, fetch) => shallowMount(componente, {
    propsData: { registro },
    mocks: { utils: { fetch } },
    stubs: { 'b-tabs': true, 'b-tab': true, 'b-badge': true }
  })

  it('LOA-PCL-105: a aba cuja requisição falha fica marcada, e as outras carregam', async () => {
    const fetch = vi.fn((pedido) => (pedido.model === 'tramitacao' ? falha(500) : Promise.resolve({ data: [{ id: 1 }] })))
    const vm = montar(PclDetalheEmenda, registroEmenda(), fetch).vm

    vm.fetchTabData(vm.registro)
    await esperar(10)

    expect(vm.erros).toEqual({ tramitacoes: true })
    expect(vm.tramitacoesItems).toBe(null)
    expect(vm.prestacaoItems).toEqual([{ id: 1 }])
    expect(vm.empenhosItems).toEqual([{ id: 1 }])
  })

  it('LOA-PCL-105: falha nos empenhos ou nos ajustes da emenda marca a aba de cada um', async () => {
    const semEmpenhos = vi.fn((p) => (p.model === 'empenhoemendaajuste' ? falha(500) : Promise.resolve({ data: [] })))
    const a = montar(PclDetalheEmenda, registroEmenda(), semEmpenhos).vm
    a.fetchTabData(a.registro)
    await esperar(10)
    expect(a.erros).toEqual({ empenhos: true })

    const semAjustes = vi.fn((p) => (p.model === 'registroajusteloa' ? falha(500) : Promise.resolve({ data: [{ id: 3 }] })))
    const b = montar(PclDetalheEmenda, registroEmenda(), semAjustes).vm
    b.fetchTabData(b.registro)
    await esperar(10)
    expect(b.erros).toEqual({ ajustes: true })
    // os empenhos da própria emenda saem mesmo sem a lista de ajustes
    expect(b.empenhosItems).toEqual([{ id: 3 }])
  })

  it('LOA-PCL-105: tentar de novo limpa a marca e busca outra vez', async () => {
    let quebrado = true
    const fetch = vi.fn(() => (quebrado ? falha(500) : Promise.resolve({ data: [{ id: 5 }] })))
    const registro = { __label__: 'loa_registroajusteloa', id: 21, tipo: 99, fase: 60, abas: { prestacao: 1, empenhos: 0 } }
    const vm = montar(PclDetalheAjuste, registro, fetch).vm

    vm.fetchTabData(vm.registro)
    await esperar(10)
    expect(vm.erros).toEqual({ prestacao: true })

    quebrado = false
    vm.fetchTabData(vm.registro)
    await esperar(10)
    expect(vm.erros).toEqual({})
    expect(vm.prestacaoItems).toEqual([{ id: 5 }])
  })

  it('LOA-PCL-105: toda aba com falha mostra o aviso e pede para tentar de novo', async () => {
    for (const aba of [PclTabPrestacao, PclTabAjustes, PclTabEmpenhos, PclTabDocumentos, PclTabTramitacoes]) {
      const wrapper = mount(aba, { propsData: { items: null, erro: true }, stubs: { 'b-spinner': true } })

      expect(wrapper.find('.pcl-aba-erro').text()).toContain('Não foi possível carregar.')
      expect(wrapper.text()).not.toContain('Carregando...')
      await wrapper.find('.pcl-aba-erro a').trigger('click')
      expect(wrapper.emitted('tentar')).toHaveLength(1)

      const carregando = mount(aba, { propsData: { items: null }, stubs: { 'b-spinner': true } })
      expect(carregando.find('.pcl-aba-erro').exists()).toBe(false)
      expect(carregando.text()).toContain('Carregando...')
    }
  })
})
