import EmendaLoaList from './EmendaLoaList'
import EmendaLoaCreate from './EmendaLoaCreate'
import EmendaLoaUpdate from './EmendaLoaUpdate'

export default class EmendaLoaCRUD {
  constructor () {
    const container = $('.container-loa')
    if (container.hasClass('emendaloa-update')) {
      this.EmendaLoaUpdate = new EmendaLoaUpdate(container)
    } else if (container.hasClass('emendaloa-create')) {
      this.EmendaLoaCreate = new EmendaLoaCreate(container)
    } else if (container.hasClass('emendaloa-list')) {
      this.EmendaLoaList = new EmendaLoaList(container)
    }
  }
}
