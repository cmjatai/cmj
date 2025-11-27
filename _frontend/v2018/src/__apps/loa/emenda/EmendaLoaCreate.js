import EmendaLoaForm from './EmendaLoaForm'

export default class EmendaLoaCreate extends EmendaLoaForm {
  constructor (container) {
    super(container)
    this.init()
  }

  init () {
    this.toggleTipo()
  }
}
