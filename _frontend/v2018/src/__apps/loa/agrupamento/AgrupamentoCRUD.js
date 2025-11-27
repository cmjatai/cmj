import AgrupamentoUpdate from './AgrupamentoUpdate'

export default class AgrupamentoCRUD {
  constructor () {
    const container = $('.container-loa')
    if (container.hasClass('agrupamento-update')) {
      this.AgrupamentoUpdate = new AgrupamentoUpdate(container)
    }
  }
}
