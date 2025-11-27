export default class EmendaLoaForm {
  constructor (container) {
    this.container = container
    this.form = container.find('form')
  }

  toggleTipo () {
    const form = this.form
    const select_tipo = form.find('select[name="tipo"]')[0]
    const div_id_parl_assinantes = form.find('#div_id_parl_assinantes')
    const div_id_parlamentares__valor = form.find('#div_id_parlamentares__valor')
    const input_valor = form.find('input[name="valor"]')[0]

    if (select_tipo.value !== '0') {
      if (div_id_parl_assinantes.length > 0) {
        input_valor.setAttribute('readonly', 'readonly')
        div_id_parl_assinantes.find('input').prop('disabled', true)
        div_id_parl_assinantes[0].classList.add('d-none')
      }
    } else {
      if (div_id_parlamentares__valor.length > 0) {
        input_valor.removeAttribute('readonly')
        div_id_parlamentares__valor.find('input').prop('disabled', true)
        div_id_parlamentares__valor[0].classList.add('d-none')
      }
    }

    form.find('select[name="tipo"]').change((event) => {
      const select = event.target
      if (select.value === '0') {
        div_id_parlamentares__valor.find('input').prop('disabled', true)
        div_id_parlamentares__valor[0].classList.add('d-none')

        div_id_parl_assinantes[0].classList.remove('d-none')
        div_id_parl_assinantes.find('input').prop('disabled', false)

        input_valor.removeAttribute('readonly')
      } else {
        div_id_parl_assinantes.find('input').prop('disabled', true)
        div_id_parl_assinantes[0].classList.add('d-none')

        div_id_parlamentares__valor[0].classList.remove('d-none')
        div_id_parlamentares__valor.find('input').prop('disabled', false)

        input_valor.setAttribute('readonly', 'readonly')
      }
    })
  }
}
