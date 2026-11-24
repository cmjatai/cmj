import { shallowMount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import PclDetalheAjuste from '@/modules/loa/pcl/PclDetalheAjuste.vue'
import PclDetalheEmenda from '@/modules/loa/pcl/PclDetalheEmenda.vue'
import PrestacaoContaLoaLayout from '@/modules/loa/pcl/PrestacaoContaLoaLayout.vue'

import { esperar } from '../../apoio'

const metodos = PrestacaoContaLoaLayout.methods
// Resposta de prestacaoconta_opcoes
const OPCOES = {
  parlamentares: [{ id: 1, nome: 'Ana' }, { id: 2, nome: 'Beto' }],
  unidades: [{ id: 7, nome: '01 - Saúde', ano: 2026 }],
  entidades: [{ id: 3, nome: 'Casa Abrigo', rotulo: 'Casa Abrigo - CNPJ: 00.000.000/0001-00' }]
}

// Itens de prestacaoconta_itens (docs/specs/loa/prestacao-contas-consulta.md).
const itemEmenda = (mudancas = {}) => ({
  classe: 'emenda',
  id: 11,
  loa: { id: 2026, ano: 2026 },
  titulo: 'EMI 012/2026',
  link: '/loa/emendaloa/11',
  tipo: 99,
  tipo_rotulo: 'Em.Imp. Áreas Diversas',
  fase: 30,
  fase_rotulo: 'Aprovada',
  valor_original: '1500.00',
  valor_final: '0.00',
  tem_ajustes: true,
  parlamentares: [{ id: 1, nome: 'Ana', fotografia: '/api/parlamentares/parlamentar/1/fotografia.png', valor: '1500.00' }],
  unidade: { id: 7, nome: '01 - Saúde' },
  entidade: { id: 3, nome: 'Casa Abrigo' },
  objeto: 'Altera destinação de recursos.',
  materia: 900,
  abas: { prestacao: 0, ajustes: 2, empenhos: 3, tramitacoes: 4, documentos: 0 },
  ...mudancas
})
const itemAjuste = (mudancas = {}) => ({
  classe: 'ajuste',
  id: 21,
  loa: { id: 2026, ano: 2026 },
  titulo: 'RAT 002/2026 - Registro de Ajuste Técnico',
  link: '/loa/registroajusteloa/21',
  tipo: 99,
  tipo_rotulo: 'Áreas Diversas',
  fase: 99,
  fase_rotulo: 'Finalizado',
  valor: '-250.00',
  valor_final: '-250.00',
  parlamentares: [{ id: 2, nome: 'Beto', fotografia: null, valor: '-250.00' }],
  unidade: null,
  entidade: null,
  emendas: [{ id: 11, titulo: 'EMI 012/2026' }],
  descricao: 'Remanejamento',
  abas: { prestacao: 1, empenhos: 0 },
  ...mudancas
})

const painel = (mudancas = {}) => ({
  loa: { id: 2026 },
  selected_loa_ids: [2026],
  filters_value: { unidade: null, entidade: null, parlamentares: null, situacao: [], emendas_tipos: ['99'], ajustes: 'False', search: '' },
  itens: ['antigos'],
  total_itens: 99,
  resumo: 'anterior',
  dashboard: null,
  viewMode: 'list',
  fetching: false,
  firstPageLoaded: true,
  currentPage: 2,
  pageSize: 25,
  _fetchId: 5,
  getResumoParams: metodos.getResumoParams,
  registrarFalha: metodos.registrarFalha,
  registroDoItem: metodos.registroDoItem,
  ...mudancas
})
const resposta = (results, total) => ({ data: { pagination: { total_entries: total }, results } })

describe('lista de cartões da prestação de contas', () => {
  it('LOA-PCL-098: o item da emenda chega ao cartão com os valores decididos pelo backend', () => {
    const registro = metodos.registroDoItem(itemEmenda())

    expect(registro).toMatchObject({
      __label__: 'loa_emendaloa',
      id: 11,
      _loa_id: 2026,
      link_detail_backend: '/loa/emendaloa/11',
      epigrafe_short: 'EMI 012/2026',
      materia: { id: 900 },
      fase_rotulo: 'Aprovada',
      str_valor: '1.500,00',
      str_valor_computado: '0,00',
      valor_computado: 0,
      has_ajustes: true,
      ementa_format: 'Altera destinação de recursos.',
      unidade: { id: 7, __str__: '01 - Saúde' },
      entidade: { id: 3, nome_fantasia: 'Casa Abrigo' },
      abas: { ajustes: 2, empenhos: 3 }
    })
    expect(registro.parlamentares[0]).toMatchObject({ id: 1, __str__: 'Ana' })
    expect(metodos.registroDoItem(itemEmenda({ materia: null, entidade: null, unidade: null }))).toMatchObject({
      materia: null,
      entidade: null,
      unidade: null
    })
  })

  it('LOA-PCL-098: o item do ajuste traz as emendas vinculadas e o valor negativo entre parênteses', () => {
    const registro = metodos.registroDoItem(itemAjuste())

    expect(registro).toMatchObject({
      __label__: 'loa_registroajusteloa',
      __str__: 'RAT 002/2026 - Registro de Ajuste Técnico',
      fase_rotulo: 'Finalizado',
      str_valor: '(250,00)',
      str_valor_computado: '-250,00',
      emendaloa: [{ id: 11, __str__: 'EMI 012/2026' }],
      descricao: 'Remanejamento',
      abas: { prestacao: 1, empenhos: 0 }
    })
    expect(registro.parlamentares_valor[0]).toMatchObject({ id: 2, __str__: 'Beto' })
    expect(metodos.registroDoItem(itemAjuste({ valor: '70.00', valor_final: '0.00' }))).toMatchObject({
      str_valor: '70,00',
      str_valor_computado: '0,00'
    })
  })

  it('LOA-PCL-099: pede ao backend só a página em exibição, com os filtros da busca', async () => {
    const fetch = vi.fn(() => Promise.resolve(resposta([itemEmenda(), itemAjuste()], 137)))
    const p = painel({ utils: { fetch } })

    await metodos.fetchItens.call(p, 5)

    expect(fetch).toHaveBeenCalledWith({
      app: 'loa',
      model: 'loa',
      id: 2026,
      action: 'prestacaoconta_itens',
      params: { tipo__in: '99', page: 2, page_size: 25 }
    })
    expect(p.itens.map(i => [i.__label__, i.id])).toEqual([['loa_emendaloa', 11], ['loa_registroajusteloa', 21]])
    expect(p.total_itens).toBe(137)
    expect(p.fetching).toBe(false)
  })

  it('LOA-PCL-099: descarta a resposta de uma busca ou de uma página anterior, e a falha esvazia a lista', async () => {
    const lenta = vi.fn(() => esperar(20).then(() => resposta([itemEmenda()], 1)))
    const rapida = vi.fn(() => Promise.resolve(resposta([itemAjuste()], 1)))
    const p = painel({ utils: { fetch: lenta } })
    const primeira = metodos.fetchItens.call(p, 5)
    p.utils = { fetch: rapida }
    await metodos.fetchItens.call(p, 5)
    await primeira
    expect(p.itens.map(i => i.id)).toEqual([21])

    const deOutraBusca = painel({ utils: { fetch: rapida } })
    await metodos.fetchItens.call(deOutraBusca, 4)
    expect(deOutraBusca.itens).toEqual(['antigos'])

    const falha = painel({ utils: { fetch: vi.fn(() => Promise.reject(new Error('rede'))) } })
    await metodos.fetchItens.call(falha, 5)
    expect([falha.itens, falha.total_itens, falha.fetching]).toEqual([[], 0, false])
  })

  it('LOA-PCL-099: trocar de página ou de tamanho busca a página no backend', () => {
    const guardado = vi.spyOn(Storage.prototype, 'setItem')
    const p = painel({ fetchItens: vi.fn(), total_itens: 137 })

    metodos.onPageChange.call(p, 99)
    expect(p.currentPage).toBe(6)
    expect(p.fetchItens).toHaveBeenLastCalledWith(5)

    metodos.onPageChange.call(p, 0)
    expect(p.currentPage).toBe(1)

    metodos.onPageSizeChange.call(p, 50)
    expect([p.pageSize, p.currentPage]).toEqual([50, 1])
    expect(guardado).toHaveBeenCalledWith('portalcmj_page_size', 50)
    expect(p.fetchItens).toHaveBeenCalledTimes(3)
    guardado.mockRestore()
  })

  it('LOA-PCL-099: uma busca pede o resumo e a primeira página juntos, sem carregar a LOA inteira', async () => {
    const p = painel({
      fetchResumo: vi.fn(() => Promise.resolve()),
      fetchItens: vi.fn(() => Promise.resolve())
    })

    await metodos.fetch.call(p)

    expect(p._fetchId).toBe(6)
    expect(p.fetchResumo).toHaveBeenCalledWith(6)
    expect(p.fetchItens).toHaveBeenCalledWith(6)
    expect([p.itens, p.total_itens, p.resumo, p.firstPageLoaded]).toEqual([[], 0, null, true])
  })
})

describe('cartões da prestação de contas', () => {
  beforeEach(() => {
    // o jsdom não tem IntersectionObserver; os cartões o usam para a carga das abas
    vi.stubGlobal('IntersectionObserver', class {
      observe () {}
      disconnect () {}
    })
  })
  afterEach(() => vi.unstubAllGlobals())

  const stubs = { 'b-tabs': true, 'b-tab': true, 'b-badge': true }
  const montar = (componente, item, fetch) => shallowMount(componente, {
    propsData: { registro: metodos.registroDoItem(item) },
    mocks: { utils: { fetch } },
    stubs
  })
  const pedidos = (fetch) => fetch.mock.calls.map(c => [c[0].model, Object.keys(c[0].params)[0], Object.values(c[0].params)[0]])

  it('LOA-PCL-100: o cartão mostra o rótulo da fase que veio do backend', () => {
    const fetch = vi.fn(() => Promise.resolve({ data: [] }))

    expect(montar(PclDetalheAjuste, itemAjuste(), fetch).text()).toContain('Finalizado')
    expect(montar(PclDetalheEmenda, itemEmenda({ fase_rotulo: 'Aprovada no Processo Legislativo' }), fetch).text())
      .toContain('Aprovada no Processo Legislativo')
  })

  it('LOA-PCL-101: a ordem das abas da emenda sai das contagens, antes de qualquer requisição', () => {
    const fetch = vi.fn(() => Promise.resolve({ data: [] }))
    const vm = montar(PclDetalheEmenda, itemEmenda(), fetch).vm

    expect(vm.orderedTabs.map(t => [t.key, t.hasData])).toEqual([
      ['ajustes', true],
      ['empenhos', true],
      ['prestacao', false],
      ['tramitacoes', true],
      ['documentos', false]
    ])
    expect(vm.contagem('empenhos')).toBe(3)
    expect(fetch).not.toHaveBeenCalled()

    const semMateria = montar(PclDetalheEmenda, itemEmenda({ materia: null }), fetch).vm
    expect(semMateria.orderedTabs.map(t => t.key)).toEqual(['ajustes', 'empenhos', 'prestacao'])
  })

  it('LOA-PCL-101: aba vazia não gera requisição, e os empenhos esperam os ajustes da emenda', async () => {
    const fetch = vi.fn((pedido) => {
      const { model, params } = pedido
      if (model === 'registroajusteloa') return esperar(15).then(() => ({ data: [{ id: 21 }, { id: 22 }] }))
      if (model === 'empenhoemendaajuste' && params.emendaloa) return Promise.resolve({ data: [{ id: 1 }] })
      if (model === 'empenhoemendaajuste' && params.ajuste === 21) return Promise.resolve({ data: [{ id: 1 }, { id: 2 }] })
      if (model === 'empenhoemendaajuste') return Promise.resolve({ data: [{ id: 3 }] })
      return Promise.resolve({ data: [{ id: 9 }] })
    })
    const vm = montar(PclDetalheEmenda, itemEmenda(), fetch).vm

    vm.fetchTabData(vm.registro)
    await esperar(40)

    // prestação de contas e documentos têm contagem zero: nenhuma requisição
    expect(pedidos(fetch).sort()).toEqual([
      ['empenhoemendaajuste', 'ajuste', 21],
      ['empenhoemendaajuste', 'ajuste', 22],
      ['empenhoemendaajuste', 'emendaloa', 11],
      ['registroajusteloa', 'emendaloa', 11],
      ['tramitacao', 'materia', 900]
    ])
    expect([vm.prestacaoItems, vm.documentosItems]).toEqual([[], []])
    expect(vm.ajustesItems.map(a => a.id)).toEqual([21, 22])
    // os da emenda e os dos ajustes, sem repetir, mesmo com a lista de ajustes chegando depois
    expect(vm.empenhosItems.map(e => e.id)).toEqual([1, 2, 3])
    expect(vm.contagem('empenhos')).toBe(3)
  })

  it('LOA-PCL-101: as abas do ajuste aparecem pelas contagens, e a vazia não gera requisição', async () => {
    const fetch = vi.fn(() => Promise.resolve({ data: [{ id: 5 }] }))
    const comAbas = montar(PclDetalheAjuste, itemAjuste(), fetch).vm

    expect(comAbas.hasTabs).toBe(true)
    comAbas.fetchTabData(comAbas.registro)
    await esperar()
    expect(pedidos(fetch)).toEqual([['prestacaocontaregistro', 'registro_ajuste', 21]])
    expect(comAbas.empenhosItems).toEqual([])

    const semAbas = montar(PclDetalheAjuste, itemAjuste({ abas: { prestacao: 0, empenhos: 0 } }), fetch).vm
    expect(semAbas.hasTabs).toBe(false)
  })
})

describe('montagem do painel', () => {
  const montarPainel = (fetch, query = {}) => shallowMount(PrestacaoContaLoaLayout, {
    mocks: {
      $route: { params: { pkloa: 2026 }, query },
      $router: { replace: vi.fn(() => Promise.resolve()) },
      utils: { fetch },
      removeAside: vi.fn()
    }
  })
  const backend = (exercicios) => vi.fn((pedido) => {
    if (pedido.action === 'prestacaoconta_resumo') {
      if (exercicios === null) return Promise.reject(new Error('404'))
      return Promise.resolve({ data: { exercicios, itens: 0 } })
    }
    if (pedido.action === 'prestacaoconta_opcoes') return Promise.resolve({ data: OPCOES })
    if (pedido.action === 'prestacaoconta_itens') return Promise.resolve(resposta([], 0))
    return Promise.resolve({ data: { id: pedido.id, ano: pedido.id, parlamentares: [] } })
  })

  it('LOA-PCL-102: os botões de exercício vêm do backend, e a URL só acrescenta exercícios disponíveis', async () => {
    const fetch = backend([
      { id: 2026, ano: 2026, selecionado: true },
      { id: 2025, ano: 2025, selecionado: false }
    ])
    const wrapper = montarPainel(fetch, { loas: '2025,2027' })
    await esperar(10)

    expect(wrapper.vm.loas_choice).toEqual([{ value: 2026, text: 2026 }, { value: 2025, text: 2025 }])
    // 2027 não está entre os disponíveis: fica de fora
    expect(wrapper.vm.selected_loa_ids).toEqual([2026, 2025])
    const modelos = fetch.mock.calls.map(c => [c[0].model, c[0].action || 'detalhe'])
    expect(modelos).not.toContainEqual(['emendaloa', 'detalhe'])
    expect(modelos).not.toContainEqual(['registroajusteloa', 'detalhe'])
    expect(fetch.mock.calls.filter(c => c[0].action === 'prestacaoconta_itens')[0][0].params).toMatchObject({
      loas: '2025',
      page: 1
    })
  })

  it('LOA-PCL-102: sem prestação de contas para a LOA da rota, não há exercícios nem itens', async () => {
    const wrapper = montarPainel(backend(null))
    await esperar(10)

    expect(wrapper.vm.loas_choice).toEqual([])
    expect([wrapper.vm.itens, wrapper.vm.resumo, wrapper.vm.ready]).toEqual([[], null, true])
  })
})

describe('filtros vindos da URL', () => {
  afterEach(() => vi.useRealTimers())

  const esperar10s = (select, depois) => {
    vi.useFakeTimers()
    const p = { filters_value: { unidade: null }, aplicarFiltroQuandoHouverOpcao: metodos.aplicarFiltroQuandoHouverOpcao }
    metodos.aplicarFiltroQuandoHouverOpcao.call(p, 'unidade', 7, select)
    if (depois) depois()
    return p
  }

  it('LOA-PCL-103: aplica o filtro quando a opção do id pedido aparece no seletor', () => {
    const select = { options: [{ value: null }] }
    const p = esperar10s(select)

    vi.advanceTimersByTime(300)
    expect(p.filters_value.unidade).toBe(null)

    select.options.push({ value: { id: 7, __str__: '01 - Saúde' } })
    vi.advanceTimersByTime(100)
    expect(p.filters_value.unidade).toEqual({ id: 7, __str__: '01 - Saúde' })
    expect(vi.getTimerCount()).toBe(0)
  })

  it('LOA-PCL-103: desiste depois de 10 segundos se a opção não existe', () => {
    const p = esperar10s({ options: [{ value: { id: 8 } }] })

    vi.advanceTimersByTime(9800)
    expect(vi.getTimerCount()).toBe(1)

    vi.advanceTimersByTime(200)
    expect(vi.getTimerCount()).toBe(0)
    expect(p.filters_value.unidade).toBe(null)
  })
})

describe('opções dos filtros', () => {
  const montarPainel = (fetch, query = {}) => shallowMount(PrestacaoContaLoaLayout, {
    mocks: {
      $route: { params: { pkloa: 2026 }, query },
      $router: { replace: vi.fn(() => Promise.resolve()) },
      utils: { fetch },
      removeAside: vi.fn()
    }
  })
  const backend = (opcoesPor = () => OPCOES) => vi.fn((pedido) => {
    if (pedido.action === 'prestacaoconta_resumo') {
      return Promise.resolve({
        data: {
          exercicios: [{ id: 2026, ano: 2026, selecionado: true }, { id: 2025, ano: 2025, selecionado: false }],
          itens: 0
        }
      })
    }
    if (pedido.action === 'prestacaoconta_opcoes') return Promise.resolve({ data: opcoesPor(pedido) })
    if (pedido.action === 'prestacaoconta_itens') return Promise.resolve(resposta([], 0))
    return Promise.resolve({ data: { id: 2026, ano: 2026 } })
  })
  const pedidosDeOpcoes = (fetch) => fetch.mock.calls.filter(c => c[0].action === 'prestacaoconta_opcoes').map(c => c[0].params)

  it('LOA-PCL-106: os três seletores recebem as opções do backend', async () => {
    const fetch = backend()
    const wrapper = montarPainel(fetch)
    await esperar(10)

    expect(pedidosDeOpcoes(fetch)).toEqual([{}])
    expect(wrapper.vm.parlamentares_choice.map(o => o.text)).toEqual(['----------------', 'Ana', 'Beto'])
    expect(wrapper.vm.unidades_choice.map(o => o.text)).toEqual(['----------------', '01 - Saúde'])
    expect(wrapper.vm.entidades_choice).toEqual([
      { value: null, text: '----------------' },
      {
        value: { id: 3, nome_fantasia: 'Casa Abrigo', __str__: 'Casa Abrigo - CNPJ: 00.000.000/0001-00' },
        text: 'Casa Abrigo - CNPJ: 00.000.000/0001-00'
      }
    ])
    // nenhuma requisição às rotas de entidade, de unidade ou ao detalhe com parlamentares
    expect(fetch.mock.calls.map(c => c[0].model)).toEqual(expect.not.arrayContaining(['entidade', 'unidadeorcamentaria']))
  })

  it('LOA-PCL-106: o filtro de parlamentar da URL é lido das opções', async () => {
    const wrapper = montarPainel(backend(), { parlamentares: '2' })
    await esperar(10)

    expect(wrapper.vm.filters_value.parlamentares).toMatchObject({ id: 2, nome_parlamentar: 'Beto' })
  })

  it('LOA-PCL-106: trocar de exercício pede as opções de novo e descarta o filtro que ficou sem opção', async () => {
    const soDe2026 = { ...OPCOES, entidades: [] }
    const fetch = backend(pedido => (pedido.params && pedido.params.loas ? OPCOES : soDe2026))
    const wrapper = montarPainel(fetch, { loas: '2025' })
    await esperar(10)
    const entidade = wrapper.vm.entidades_choice[1].value
    wrapper.vm.filters_value = { ...wrapper.vm.filters_value, entidade }
    await esperar(10)

    await wrapper.vm.on_loas_change([2026])
    await esperar(10)

    expect(pedidosDeOpcoes(fetch)).toEqual([{ loas: '2025' }, {}])
    expect(wrapper.vm.entidades_choice).toHaveLength(1)
    expect(wrapper.vm.filters_value.entidade).toBe(null)
    const ultimaBusca = fetch.mock.calls.filter(c => c[0].action === 'prestacaoconta_itens').pop()[0].params
    expect(ultimaBusca.entidade).toBeUndefined()
  })
})
