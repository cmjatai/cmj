import EmpenhoUpdate from './EmpenhoUpdate'

export default class EmendaLoaCRUD {
  constructor () {
    const container = $('.container-loa')
    if (container.hasClass('empenho-update')) {
      this.EmpenhoUpdate = new EmpenhoUpdate(container)
    }
  }
}
