import $ from 'jquery'
import axios from 'axios'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import AgrupamentoUpdate from '@/__apps/loa/agrupamento/AgrupamentoUpdate'

vi.mock('axios', () => ({
  default: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), delete: vi.fn() }
}))

const PK = '7'

const emenda = (id, fase, agrupamento = null) => ({
  id,
  fase,
  agrupamento,
  tipo: 99,
  str_valor: '1.000,00',
  indicacao: `Indicação ${id}`,
  prefixo_finalidade: '',
  finalidade: 'Finalidade',
  str_parlamentares: ['Parlamentar A'],
  str_fase: `Fase ${fase}`,
  link_detail_backend: `/loa/emendaloa/${id}`,
  permite_juncao_coletiva: true
})

const DO_AGRUPAMENTO = { id: 7, nome: 'Este', link_detail_backend: '/loa/agrupamento/7' }
const OUTRO = { id: 9, nome: 'Outro', link_detail_backend: '/loa/agrupamento/9' }

// Selecionadas: uma na 15 e uma já transformada em coletiva (-10).
// Busca: uma na 12, uma na 10 e uma de outro agrupamento, que o servidor manda no fim.
const SELECIONADAS = [emenda(1, 15, DO_AGRUPAMENTO), emenda(2, -10, DO_AGRUPAMENTO)]
const BUSCA = [emenda(3, 12), emenda(4, 10), emenda(5, 15, OUTRO)]

const flush = async () => {
  for (let i = 0; i < 5; i++) await new Promise((resolve) => setTimeout(resolve, 0))
}

const montarTela = async () => {
  document.body.innerHTML = `
    <div class="container-loa agrupamento-update">
      <form>
        <input type="hidden" name="ano_loa" value="2027">
        <textarea name="finalidade" id="id_finalidade"></textarea>
        <input type="text" name="busca_emendaloa">
        <div class="busca-render-emendaloa"></div>
        <div class="emendaloa-selecteds"></div>
        <div class="registro-render"></div>
      </form>
    </div>`
  const tela = new AgrupamentoUpdate($('.container-loa'))
  await flush()
  $('input[name="busca_emendaloa"]').val('Parlamentar').trigger('keyup')
  await flush()
  return tela
}

const item = (pk) => $(`.item-emendaloa[pk="${pk}"]`).closest('.inner-item')
const botoes = (pk) => item(pk).find('.inner-actions .btn').toArray()
  .map((el) => (el.classList.contains('btn-devolver') ? 'devolver' : el.classList.contains('btn-delete') ? 'lixeira' : 'seta'))

describe('devolução para correção pela tela do agrupamento', () => {
  beforeEach(() => {
    window.history.pushState({}, '', `/loa/agrupamento/${PK}/edit`)
    axios.get.mockImplementation((url) => {
      if (url.includes('/emendas/')) return Promise.resolve({ data: SELECIONADAS })
      if (url.includes('/emendaloa/search/')) return Promise.resolve({ data: BUSCA })
      if (url === `/api/loa/agrupamento/${PK}/`) return Promise.resolve({ data: { finalidade: '' } })
      return Promise.resolve({ data: [] })
    })
  })

  afterEach(() => {
    document.body.innerHTML = ''
    vi.restoreAllMocks()
    axios.get.mockReset()
    axios.post.mockReset()
  })

  it('LOA-AGR-091: o botão de devolver fica abaixo da seta e da lixeira, só nas fases 12, 15 e 17', async () => {
    await montarTela()

    expect(botoes(1)).toEqual(['lixeira', 'devolver'])
    expect(botoes(2)).toEqual(['lixeira'])
    expect(botoes(3)).toEqual(['seta', 'devolver'])
    expect(botoes(4)).toEqual([])
  })

  it('LOA-AGR-096: a emenda de outro agrupamento aparece só como informação, com o agrupamento', async () => {
    await montarTela()

    expect(botoes(5)).toEqual([])
    const link = item(5).find('.agrupamento-da-emenda a')
    expect(item(5).find('.agrupamento-da-emenda').text()).toBe('No agrupamento Outro')
    expect(link.attr('href')).toBe('/loa/agrupamento/9')
  })

  it('LOA-AGR-093: confirma, devolve, tira a emenda da busca e mostra a mensagem verde', async () => {
    await montarTela()
    const confirmar = vi.spyOn(window, 'confirm').mockReturnValue(true)
    axios.post.mockResolvedValue({
      data: { detail: 'Emenda devolvida para correção com sucesso.', saiu_do_agrupamento: false, aviso_finalidade: '' }
    })

    item(3).find('.btn-devolver').trigger('click')
    await flush()

    expect(confirmar).toHaveBeenCalledWith('Devolver a Emenda R$ 1.000,00 - Indicação 3 para correção pelo autor?')
    expect(axios.post).toHaveBeenCalledWith(`/api/loa/agrupamento/${PK}/devolver_emenda/`, { emendaloa: 3 })
    expect(item(3).length).toBe(0)
    const sucesso = $('.agrupamento-mensagens .alert-success')
    expect(sucesso.length).toBe(1)
    expect(sucesso.text()).toContain('Emenda devolvida para correção com sucesso.')
  })

  it('LOA-AGR-093: sem a confirmação nada é enviado', async () => {
    await montarTela()
    vi.spyOn(window, 'confirm').mockReturnValue(false)

    item(1).find('.btn-devolver').trigger('click')
    await flush()

    expect(axios.post).not.toHaveBeenCalled()
    expect(item(1).length).toBe(1)
  })

  it('LOA-AGR-093: a recusa do servidor aparece como mensagem de erro e a emenda fica na lista', async () => {
    await montarTela()
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    axios.post.mockRejectedValue({ response: { status: 400, data: ['A Emenda Coletiva não pode ser devolvida.'] } })

    item(1).find('.btn-devolver').trigger('click')
    await flush()

    expect(item(1).length).toBe(1)
    const erro = $('.agrupamento-mensagens .alert-danger')
    expect(erro.text()).toContain('Não foi possível devolver a Emenda.')
    expect(erro.text()).toContain('A Emenda Coletiva não pode ser devolvida.')
  })
})
