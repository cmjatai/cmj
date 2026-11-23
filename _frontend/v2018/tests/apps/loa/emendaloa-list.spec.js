import $ from 'jquery'
import { afterEach, describe, expect, it, vi } from 'vitest'

import EmendaLoaList from '@/__apps/loa/emenda/EmendaLoaList'

// Marcação da listagem para operador de autor: o formulário POST de registro das emendas liberadas
// (LOA-LST-016) vem antes do filtro, no mesmo .container-loa.
const montarTela = () => {
  document.body.innerHTML = `
    <div class="container-loa emendaloa-list">
      <form method="post" class="form-register-emendas-liberadas">
        <button type="submit" name="registrar" value="1">Registrar Emendas Liberadas</button>
      </form>
      <form method="get" class="container form-filter-emendaloa">
        <input type="text" name="finalidade">
        <input type="text" name="outro">
        <button type="button" class="btn-filtrar">Filtrar</button>
      </form>
    </div>`
  return $('.container-loa')
}

const enter = (alvo) => $(alvo).trigger($.Event('keypress', { keyCode: 13 }))

describe('listagem de emendas da LOA', () => {
  afterEach(() => {
    document.body.innerHTML = ''
    delete window.loadingCMJ
    vi.restoreAllMocks()
  })

  it('LOA-LST-066: "Filtrar" e Enter na busca enviam só o filtro, nunca o registro das emendas liberadas', () => {
    const container = montarTela()
    window.loadingCMJ = vi.fn()
    const enviados = []
    vi.spyOn(HTMLFormElement.prototype, 'submit').mockImplementation(function () {
      enviados.push(this.className)
    })
    const registro = vi.fn()
    container.find('.form-register-emendas-liberadas').on('submit', registro)

    new EmendaLoaList(container) // eslint-disable-line no-new
    container.find('button.btn-filtrar').trigger('click')
    enter(container.find('input[name="finalidade"]'))
    enter(container.find('input[name="outro"]'))

    expect(enviados).toEqual(['container form-filter-emendaloa', 'container form-filter-emendaloa'])
    expect(registro).not.toHaveBeenCalled()
  })
})
