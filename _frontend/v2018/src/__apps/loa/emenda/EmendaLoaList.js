export default class EmendaLoaList {
  constructor (container) {
    this.container = container
    // LOA-LST-066: só o formulário do filtro; o de registro das emendas
    // liberadas (LOA-LST-016) está no mesmo container
    this.form = container.find('form.form-filter-emendaloa')
    this.init()
  }

  init () {
    const form = this.form

    // LOA-LST-067: o filtro não é lembrado entre visitas; fica só na URL.
    // Remove o filtro gravado por versões anteriores desta tela.
    localStorage.removeItem('portalcmj_emendaloa_filter')

    const changeAction = (event) => {
      window.loadingCMJ('Atualizando listagem...')
      form.submit()
    }

    const sAgrup = form.find('input[type="checkbox"][name="agrupamento"]')
    const rTipoAgrup = form.find('input[type="radio"][name="tipo_agrupamento"]')
    sAgrup.change((event) => {
      if (sAgrup.filter(':checked').length === 0) {
        rTipoAgrup.filter('[value="sem_registro"]').prop('checked', true)
      }
    }).change()

    rTipoAgrup
      .change((event) => {
        if (event.target.checked && event.target.value === 'sem_registro') {
          sAgrup.not('[value="despesa__unidade"], [value="entidade"]').prop('disabled', true).prop('checked', false).parent().addClass('d-none')
          sAgrup.filter('[value="despesa__unidade"], [value="entidade"]').prop('disabled', false).parent().removeClass('d-none')
          sAgrup.filter('[value="despesa__unidade"]').prop('checked', true)
        } else if (event.target.checked) {
          sAgrup.not('[value="entidade"]').prop('disabled', false).parent().removeClass('d-none')
          sAgrup.filter('[value="entidade"]').prop('disabled', true).prop('checked', false).parent().addClass('d-none')
          if (sAgrup.filter(':checked').length === 0) {
            if (sAgrup.length > 1) {
              $(sAgrup[1]).prop('checked', true)
            } else if (sAgrup.length > 0) {
              $(sAgrup[0]).prop('checked', true)
            }
          }
        } else {
          sAgrup.not('[value="entidade"]').prop('disabled', false).parent().removeClass('d-none')
          sAgrup.filter('[value="entidade"]').prop('disabled', true).prop('checked', false).parent().addClass('d-none')
        }
      }).change()

    form
      .find('#div_id_parlamentares input[type="checkbox"]')
      .change((event) => {
        // fazer toggle com a classe active do span dentro do label
        const checkbox = $(event.target)
        // label é o irmao mais próximo do checkbox, ou seja, o label abaixo do checkbox
        const labelSpan = checkbox.next('label').find('span')
        if (checkbox.is(':checked')) {
          labelSpan.addClass('active')
        } else {
          labelSpan.removeClass('active')
        }
      })
    // LOA-LST-066: só o botão "Filtrar" aplica o filtro; os botões criados
    // pelo bootstrap-select nos seletores não interferem
    form
      .find('button.btn-filtrar')
      .click((event) => {
        changeAction()
      })
    // Enter não envia o formulário; na busca por termos, aplica o filtro
    form.keypress((event) => {
      if (event.keyCode === 13) {
        event.preventDefault()
        if (event.target.name === 'finalidade') {
          changeAction()
        }
        return false
      }
    })
  }
}
