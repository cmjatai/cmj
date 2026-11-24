import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import PrestacaoContaLoaLayout from '@/modules/loa/pcl/PrestacaoContaLoaLayout.vue'
import PclDashboard from '@/modules/loa/pcl/dash/PclDashboard.vue'

// Resposta de prestacaoconta_dashboard (docs/specs/loa/prestacao-contas-consulta.md).
const parl = (id, nome, valor) => ({ id, nome, valor })
const dados = (mudancas = {}) => ({
  situacao: [
    {
      tipo: 10,
      grupos: [
        { chave: 'situacao-60', rotulo: 'Em Execução', quantidade: 2, valor: '600.00', parlamentares: [parl(1, 'Ana', '400.00'), parl(2, 'Beto', '200.00')] }
      ]
    },
    {
      tipo: 99,
      grupos: [
        { chave: 'emenda-30', rotulo: 'Aprovada', quantidade: 4, valor: '1000.00', parlamentares: [parl(1, 'Ana', '1000.00')] },
        { chave: 'situacao-60', rotulo: 'Em Execução', quantidade: 1, valor: '450.00', parlamentares: [parl(1, 'Ana', '450.00')] }
      ]
    }
  ],
  parlamentares: [
    {
      id: 1,
      nome: 'Ana',
      fotografia: '/api/parlamentares/parlamentar/1/fotografia.jpeg',
      valor: '1550.00',
      emendas: 2,
      ajustes: 2,
      unidades: [
        { id: 7, nome: '01 - Saúde', ano: 2026, valor: '1450.00' },
        { id: null, nome: null, ano: null, valor: '100.00' }
      ]
    },
    {
      id: 2,
      nome: 'Beto',
      fotografia: null,
      valor: '150.00',
      emendas: 1,
      ajustes: 1,
      unidades: [{ id: null, nome: null, ano: null, valor: '150.00' }]
    }
  ],
  unidades: [
    { id: 7, nome: '01 - Saúde', ano: 2026, valor: '1450.00', quantidade: 5, parlamentares: [parl(1, 'Ana', '1450.00'), parl(2, 'Beto', '0.00')] }
  ],
  entidades: [
    { id: 3, nome: 'Casa Abrigo', valor: '1000.00', quantidade: 1, parlamentares: [parl(1, 'Ana', '1000.00')] }
  ],
  ...mudancas
})

const montar = (propsData) => mount(PclDashboard, {
  propsData: { dados: dados(), selectedLoaIds: [2026], ...propsData },
  stubs: { 'pcl-totalizacao': true }
})
const sem = (t) => t.replace(/\s+/g, '')

describe('dashboard da prestação de contas', () => {
  it('LOA-PCL-094: sem dados do backend não mostra nada', () => {
    expect(montar({ dados: null }).find('.pcl-dashboard').exists()).toBe(false)
  })

  it('LOA-PCL-094: a situação por tipo vem pronta, com barras proporcionais à contagem', () => {
    const vm = montar().vm
    const [saude, diversas] = vm.faseSecoes

    expect(saude.titulo).toBe('Situação — Saúde')
    expect(saude.dados.map(g => [g.label, g.count, g.total, g.pct])).toEqual([['Em Execução', 2, 600, 100]])
    expect(diversas.dados.map(g => [g.label, g.count, g.total, g.pct])).toEqual([
      ['Aprovada', 4, 1000, 100],
      ['Em Execução', 1, 450, 25]
    ])
    expect(diversas.dados[0].parlamentares).toEqual([{ key: 1, label: 'Ana', total: 1000 }])
    expect(diversas.dados[0].color).not.toBe(diversas.dados[1].color)
  })

  it('LOA-PCL-095: por parlamentar, com um segmento por unidade e a mesma cor para a mesma unidade', () => {
    const vm = montar().vm
    const [ana, beto] = vm.parlamentarDistribuicao

    expect([ana.nome, ana.total, ana.emendas, ana.ajustes, ana.pct]).toEqual(['Ana', 1550, 2, 2, 100])
    expect(ana.segmentos.map(s => [s.key, s.label, s.total])).toEqual([
      [7, '01 - Saúde', 1450],
      ['sem-unidade', 'Sem unidade', 100]
    ])
    expect(beto.pct).toBeCloseTo(150 / 1550 * 100)
    expect(beto.segmentos[0].color).toBe(ana.segmentos[1].color)
    expect(ana.segmentos[0].color).not.toBe(ana.segmentos[1].color)

    const texto = sem(montar().text())
    expect(texto).toContain(sem('Ana R$ 1.550,00'))
    expect(texto).toContain(sem('2 emendas, 2 ajustes'))
    expect(texto).toContain(sem('1 emenda, 1 ajuste'))
  })

  it('LOA-PCL-095: com mais de um exercício, a unidade leva o ano', () => {
    const vm = montar({ selectedLoaIds: [2026, 2025] }).vm

    expect(vm.parlamentarDistribuicao[0].segmentos.map(s => s.label)).toEqual(['01 - Saúde (2026)', 'Sem unidade'])
  })

  it('LOA-PCL-096: unidades e entidades mostram as dez maiores, ou todas com filtro de parlamentar', () => {
    const muitas = Array.from({ length: 12 }, (_, i) => ({
      id: i + 1, nome: `Unidade ${i + 1}`, ano: 2026, valor: String(1200 - i * 100), quantidade: 1, parlamentares: []
    }))
    const semFiltro = montar({ dados: dados({ unidades: muitas }) }).vm
    expect(semFiltro.unidadeDistribuicao).toHaveLength(10)
    expect(semFiltro.unidadeDistribuicaoExtra).toBe(2)
    expect(semFiltro.unidadeDistribuicao[0].pct).toBe(100)
    expect(semFiltro.unidadeDistribuicao[1].pct).toBeCloseTo(1100 / 1200 * 100)

    const comFiltro = montar({ dados: dados({ unidades: muitas }), parlamentarSelecionado: { id: 1 } }).vm
    expect(comFiltro.unidadeDistribuicao).toHaveLength(12)
    expect(comFiltro.unidadeDistribuicaoExtra).toBe(0)

    const vm = montar().vm
    expect(vm.entidadeDistribuicao.map(e => [e.nome, e.total, e.count])).toEqual([['Casa Abrigo', 1000, 1]])
    expect(vm.unidadeDistribuicao[0].parlamentares).toEqual([
      { key: 1, label: 'Ana', total: 1450 },
      { key: 2, label: 'Beto', total: 0 }
    ])
  })

  it('LOA-PCL-096: os nomes continuam sendo atalhos de filtro', async () => {
    const wrapper = montar()
    const nomes = wrapper.findAll('.dash-bar-name--clickable').wrappers

    await nomes.find(n => n.text() === 'Ana').trigger('click')
    await nomes.find(n => n.text() === '01 - Saúde').trigger('click')
    await nomes.find(n => n.text() === 'Casa Abrigo').trigger('click')

    expect(wrapper.emitted('filter-parlamentar')[0][0]).toEqual({ id: 1, __str__: 'Ana' })
    expect(wrapper.emitted('filter-unidade')[0][0]).toEqual({ id: 7, __str__: '01 - Saúde' })
    expect(wrapper.emitted('filter-entidade')[0][0]).toEqual({ id: 3, __str__: 'Casa Abrigo' })
  })
})

describe('pedido do dashboard pelo painel', () => {
  const metodos = PrestacaoContaLoaLayout.methods
  const painel = (mudancas = {}) => ({
    loa: { id: 2026 },
    selected_loa_ids: [2026],
    filters_value: { unidade: null, entidade: null, parlamentares: { id: 157 }, situacao: [], emendas_tipos: [], ajustes: 'False', search: '' },
    resumo: null,
    dashboard: 'anterior',
    viewMode: 'list',
    ready: true,
    _fetchId: 3,
    utils: { fetch: vi.fn(() => Promise.resolve({ data: { ok: true } })) },
    $route: { query: {} },
    syncQueryString: vi.fn(),
    getResumoParams: metodos.getResumoParams,
    registrarFalha: metodos.registrarFalha,
    fetchConsulta: metodos.fetchConsulta,
    fetchDashboard: metodos.fetchDashboard,
    ...mudancas
  })
  const acoes = (p) => p.utils.fetch.mock.calls.map(c => c[0].action)

  it('LOA-PCL-097: no modo lista, a busca pede só o resumo e esquece o dashboard anterior', async () => {
    const p = painel()
    await metodos.fetchResumo.call(p, 3)

    expect(acoes(p)).toEqual(['prestacaoconta_resumo'])
    expect(p.dashboard).toBe(null)
  })

  it('LOA-PCL-097: no modo dashboard, a busca pede resumo e dashboard com os mesmos filtros', async () => {
    const p = painel({ viewMode: 'dashboard' })
    await metodos.fetchResumo.call(p, 3)

    expect(acoes(p)).toEqual(['prestacaoconta_resumo', 'prestacaoconta_dashboard'])
    expect(p.utils.fetch.mock.calls.map(c => c[0].params)).toEqual([{ parlamentar: 157 }, { parlamentar: 157 }])
    expect(p.dashboard).toEqual({ ok: true })
  })

  it('LOA-PCL-097: abrir o dashboard pede os dados, se ainda não chegaram para os filtros atuais', () => {
    const fechado = painel({ dashboard: null, fetchDashboard: vi.fn() })
    metodos.viewModeChange.call(fechado, 'dashboard')
    expect(fechado.fetchDashboard).toHaveBeenCalledWith(3)

    const jaCarregado = painel({ dashboard: { ok: true }, fetchDashboard: vi.fn() })
    metodos.viewModeChange.call(jaCarregado, 'dashboard')
    expect(jaCarregado.fetchDashboard).not.toHaveBeenCalled()

    const paraLista = painel({ dashboard: null, fetchDashboard: vi.fn() })
    metodos.viewModeChange.call(paraLista, 'list')
    expect(paraLista.fetchDashboard).not.toHaveBeenCalled()
  })
})
