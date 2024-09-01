import './scss/loa.scss'

import axios from 'axios'
axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'

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
      return
    }
    const pk = window.location.href.matchAll(/emendaloa\/(\d+)\//g).next().value[1]
    const urlBase = `/api/loa/emendaloa/${pk}`
    const loadPreview = function () {
      $('.container-preview').html(`
        <div class="btn-toolbar justify-content-between">
          <div class="btn-group btn-group-sm">
            <label for="id_lineHeight">
              <span>Entrelinha (%)</span>
              <input type="number"
                name="lineHeight" value="150"
                step="5"
                min="100"
                max="350"
                class="decimalinput numberinput form-control text-right"
                id="id_lineHeight">
            </label>
          </div>
        </div>
        <div class="inner-preview">
          <a class="w-100" target="_blank" href="${urlBase}/preview/">
            <img src="${urlBase}/preview/?page=1&u=${Date.now()}"/>
          </a>
        </div>
      `)
      return this
    }
    loadPreview()

    const img = $('.container-preview .inner-preview img')[0]
    const form = container.find('form')

    img.onload = function (event) {
      img.style.opacity = 1
    }

    form.change(function (event) {
      let formData = {}
      let key = event.target.name
      let value = event.target.value

      let action = '/'

      img.style.opacity = 0.35

      let parlamentar_id = event.target.getAttribute('parlamentar_id')
      if (parlamentar_id !== null) {
        formData['valor'] = value
        formData['parlamentar_id'] = parlamentar_id
        action = '/updatevalorparlamentar/'
      } else if (key === 'lineHeight') {
        img.src = `${urlBase}/preview/?page=1&lineHeight=${value}&u=${Date.now()}`
        return
      } else {
        formData[key] = value
      }

      axios.patch(`${urlBase}${action}`, formData)
        .then((response) => {
          form.find('input[name="lineHeight"]').val(response.data.metadata.style.lineHeight)
          form.find('input[name="valor"]').val(response.data.valor)
          img.src = `${urlBase}/preview/?page=1&u=${Date.now()}`
        })
        .catch(() => {
        })
    })
    form.find('input[name="valor"]').trigger('change')
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
