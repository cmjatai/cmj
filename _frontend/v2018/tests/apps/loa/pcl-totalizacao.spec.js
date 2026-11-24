import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import PrestacaoContaLoaLayout from '@/modules/loa/pcl/PrestacaoContaLoaLayout.vue'
import PclTotalizacao from '@/modules/loa/pcl/dash/PclTotalizacao.vue'

// Resposta de prestacaoconta_resumo (docs/specs/loa/prestacao-contas-consulta.md).
const resumo = (mudancas = {}) => ({
  exercicios: [{ id: 2026, ano: 2026, selecionado: true }],
  itens: 497,
  emendas: 385,
  ajustes: 112,
  impositivas: { valor: '13244688.35', quantidade: 444 },
  saude: { valor: '6699046.50', quantidade: 64 },
  areas_diversas: { valor: '6545641.85', quantidade: 380 },
  modificativas: { valor: '40164428.00', quantidade: 53 },
  emendas_com_valor_em_ajuste: { quantidade: 0, valor_original: '0.00' },
  emendas_em_impedimento: { quantidade: 0, valor_original: '0.00' },
  execucao: {
    vale: true,
    ano_inicial: 2026,
    empenhado: '6602802.45',
    liquidado: '4461842.64',
    pago_bruto: '4146016.69',
    anulado: '327316.93'
  },
  ...mudancas
})

const montar = (dados) => mount(PclTotalizacao, { propsData: { resumo: dados } })
// os blocos do HTML não têm espaço entre si: a comparação ignora os espaços
const sem = (t) => t.replace(/\s+/g, '')
const texto = (wrapper, seletor) => sem(wrapper.find(seletor).text())

describe('totalização da prestação de contas', () => {
  it('LOA-PCL-090: mostra os números do resumo, com a contagem de cada grupo', () => {
    const wrapper = montar(resumo())

    expect(texto(wrapper, '.total-registros')).toBe(sem('497 registros.'))
    expect(texto(wrapper, '.total-impositivas')).toBe(sem('Total Impositivas: R$ 13.244.688,35 (444 registros)'))
    expect(texto(wrapper, '.total-saude')).toBe(sem('Saúde: R$ 6.699.046,50 (64 registros)'))
    expect(texto(wrapper, '.total-areas_diversas')).toBe(sem('Áreas Diversas: R$ 6.545.641,85 (380 registros)'))
    expect(texto(wrapper, '.total-modificativas')).toBe(sem('Modificativas: R$ 40.164.428,00 (53 registros)'))
  })

  it('LOA-PCL-090: sem resumo ou sem itens não mostra nada, e esconde Modificativas sem valor', () => {
    expect(montar(null).find('.pcl-totalizacao').exists()).toBe(false)
    expect(montar(resumo({ itens: 0 })).find('.pcl-totalizacao').exists()).toBe(false)

    const wrapper = montar(resumo({
      itens: 1,
      impositivas: { valor: '10.00', quantidade: 1 },
      modificativas: { valor: '0.00', quantidade: 0 }
    }))
    expect(wrapper.find('.total-modificativas').exists()).toBe(false)
    expect(texto(wrapper, '.total-registros')).toBe(sem('1 registro.'))
    expect(texto(wrapper, '.total-impositivas')).toContain(sem('(1 registro)'))
  })

  it('LOA-PCL-091: a linha de execução usa os totais e o "vale" do resumo', () => {
    const wrapper = montar(resumo())
    const linha = texto(wrapper, '.linha-execucao')
    expect(linha).toContain(sem('Total Empenhado (49.85%) R$ 6.602.802,45'))
    expect(linha).toContain(sem('Total Liquidado (33.69%) R$ 4.461.842,64'))
    expect(linha).toContain(sem('Total Pago (31.30%) R$ 4.146.016,69'))
    expect(linha).toContain(sem('Total Anulado (2.47%) R$ 327.316,93'))
    expect(wrapper.find('.aviso-execucao').exists()).toBe(false)

    const antigo = montar(resumo({ execucao: { ...resumo().execucao, vale: false } }))
    expect(antigo.find('.linha-execucao').exists()).toBe(false)
    expect(texto(antigo, '.aviso-execucao')).toBe(
      sem('Totais de Empenho, Liquidação, Pagamento e Anulação computados apenas a partir da LOA 2026.')
    )

    const semEmpenho = montar(resumo({
      execucao: { vale: true, ano_inicial: 2026, empenhado: '0.00', liquidado: '0.00', pago_bruto: '0.00', anulado: '0.00' }
    }))
    expect(semEmpenho.find('.linha-execucao').exists()).toBe(false)
    expect(semEmpenho.find('.aviso-execucao').exists()).toBe(false)
  })

  it('LOA-PCL-092: avisa das emendas que contam com valor zero', () => {
    expect(montar(resumo()).find('.aviso-zeradas').exists()).toBe(false)

    const soEmendas = montar(resumo({
      ajustes: 0,
      emendas_com_valor_em_ajuste: { quantidade: 68, valor_original: '3394483.37' },
      emendas_em_impedimento: { quantidade: 1, valor_original: '108369.25' }
    }))
    const avisos = soEmendas.findAll('.aviso-zeradas small').wrappers.map(w => w.text())
    expect(avisos).toEqual([
      '68 emendas contam com valor zero (valor original de R$ 3.394.483,37): ' +
        'o valor foi remanejado para registros de ajuste, que não estão nesta seleção.',
      '1 emenda em impedimento técnico conta com valor zero (valor original de R$ 108.369,25).'
    ])

    const comAjustes = montar(resumo({
      emendas_com_valor_em_ajuste: { quantidade: 1, valor_original: '500.00' }
    }))
    expect(texto(comAjustes, '.aviso-zeradas')).toBe(
      sem('1 emenda conta com valor zero (valor original de R$ 500,00): o valor foi remanejado para registros de ajuste.')
    )
  })
})

describe('pedido do resumo pelo painel', () => {
  const metodos = PrestacaoContaLoaLayout.methods
  const painel = (mudancas = {}) => ({
    loa: { id: 2026 },
    selected_loa_ids: [2026],
    filters_value: {
      unidade: null,
      entidade: null,
      parlamentares: null,
      situacao: [],
      emendas_tipos: [],
      ajustes: 'False',
      search: ''
    },
    resumo: 'anterior',
    dashboard: 'anterior',
    viewMode: 'list',
    _fetchId: 7,
    getResumoParams: metodos.getResumoParams,
    registrarFalha: metodos.registrarFalha,
    fetchConsulta: metodos.fetchConsulta,
    fetchDashboard: metodos.fetchDashboard,
    ...mudancas
  })

  it('LOA-PCL-089: sem filtros, pede o resumo só da LOA da rota', () => {
    expect(metodos.getResumoParams.call(painel())).toEqual({})
  })

  it('LOA-PCL-089: leva os filtros da busca e os exercícios extras numa requisição só', () => {
    const params = metodos.getResumoParams.call(painel({
      selected_loa_ids: [2026, 2025, 2024],
      filters_value: {
        unidade: { id: 14 },
        entidade: { id: 3 },
        parlamentares: { id: 157 },
        situacao: ['REGISTRADO', 'EM_EXECUCAO'],
        emendas_tipos: [10, 99],
        ajustes: 'True',
        search: 'creche'
      }
    }))

    expect(params).toEqual({
      situacao: 'REGISTRADO,EM_EXECUCAO',
      unidade: 14,
      entidade: 3,
      parlamentar: 157,
      search: 'creche',
      tipo__in: '10,99',
      ajustes: 'True',
      loas: '2025,2024'
    })
  })

  it('LOA-PCL-089: guarda a resposta da busca atual e descarta a de uma busca anterior', async () => {
    const fetch = vi.fn(() => Promise.resolve({ data: resumo() }))
    const atual = painel({ utils: { fetch } })
    await metodos.fetchResumo.call(atual, 7)

    expect(fetch).toHaveBeenCalledWith({
      app: 'loa',
      model: 'loa',
      id: 2026,
      action: 'prestacaoconta_resumo',
      params: {}
    })
    expect(atual.resumo.itens).toBe(497)

    const atrasada = painel({ utils: { fetch } })
    await metodos.fetchResumo.call(atrasada, 6)
    expect(atrasada.resumo).toBe('anterior')
  })

  it('LOA-PCL-089: falha na requisição deixa a tela sem totalização', async () => {
    const falha = painel({ utils: { fetch: vi.fn(() => Promise.reject(new Error('rede'))) } })
    await metodos.fetchResumo.call(falha, 7)

    expect(falha.resumo).toBe(null)
  })
})
