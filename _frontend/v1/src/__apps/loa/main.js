import './scss/loa.scss'

window.AppLOA = function () {
  // Função única - Singleton pattern - operador new sempre devolve o mesmo objeto
  let instance

  if (!(this instanceof window.AppLOA)) {
    if (!instance) {
      instance = new window.AppLOA()
    }
    return instance
  }
  instance = this
  window.AppLOA = function () {
    return instance
  }

  instance.LoaCRUD = function () {}

  instance.EmendaLoaCRUD = function () {
    const container = $('.container-loa.emendaloa-update, .container-loa.emendaloa-create')
    if (container.length === 0) {
      return false
    }
    console.log('EmendaLOA')
    return true
  }

  instance.init = function () {
    instance.LoaCRUD()
    instance.EmendaLoaCRUD()
  }
  instance.init()
}

$(document).ready(function () {
  if ($('.container-loa').length > 0) {
    window.AppLOA()
  }
})
