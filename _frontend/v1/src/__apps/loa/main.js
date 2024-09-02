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
    const container = $('.container-loa.emendaloa-update')

    if (container.length === 0) {
      return
    }

    const form = container.find('form')

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
    }

    loadPreview()
    const preview = $('.container-preview .inner-preview img')[0]
    preview.onload = function (event) {
      preview.style.opacity = 1
    }

    const refreshChangeRegistroDespesa = () => {
      const rcs = form.find('input[name="registrocontabil_set"]')
      rcs.off('change')
      rcs.change((event) => {
        const pk = event.target.value
        axios.delete(`/api/loa/emendaloaregistrocontabil/${pk}/`)
          .then((response) => {
            event.target.parentElement.remove()
          })
      })
    }
    refreshChangeRegistroDespesa()

    const ano_loa = form.find('input[name="ano_loa"')[0].value
    const busca_render = form.find('.busca-render')
    const busca_despesa = form.find('input[name="busca_despesa"]')

    const add_registro = form.find('#add_registro')
    add_registro.click((event) => {
      let pk_despesa = add_registro[0].data
      console.log(pk_despesa)
      let formData = {}
      formData.emendaloa = pk
      formData.despesa = pk_despesa
      formData.codigo = form.find('input[name="despesa_codigo"]').val()
      formData.unidade = form.find('input[name="despesa_unidade"]').val()
      formData.especificacao = form.find('input[name="despesa_especificacao"]').val()
      formData.natureza = form.find('input[name="despesa_natureza"]').val()
      formData.valor = form.find('input[name="valor_despesa"]').val()
      busca_render.html('')
      const inner = $('<div class="inner"></div>')
      axios.post(`/api/loa/emendaloaregistrocontabil/create_for_emendaloa_update/`, formData)
        .then((response) => {
          add_registro[0].data = null
          form.find('input[name^="despesa_"]').attr('readonly', false)
          form.find('input[name^="despesa_"], input[name="valor_despesa"]').val('')
          $('<div class="alert alert-info">Registro de Despesa Adicionado com sucesso.</div>'
          ).appendTo(inner)

          let rcs = form.find('input[name="registrocontabil_set"]')

          let checkboxRc = $(`
            <div class="custom-control custom-checkbox">
              <input type="checkbox" class="custom-control-input" checked="checked" name="registrocontabil_set" id="id_registrocontabil_set_${rcs.length + 1}" value="${response.data.id}">
              <label class="custom-control-label" for="id_registrocontabil_set_${rcs.length + 1}">
                ${response.data.__str__}
              </label>
            </div>
          `)

          if (rcs.length > 0) {
            checkboxRc.appendTo(rcs.last().parent().parent())
          } else {
            checkboxRc.appendTo(form.find('#div_id_registrocontabil_set > div'))
          }

          refreshChangeRegistroDespesa()
        })
        .catch((error) => {
          if (_.isString(error.response.data)) {
            $(`<div class="alert alert-danger">
              ${error.message}
              </div>`
            ).appendTo(inner)
            return
          }
          _.forOwn(error.response.data, function (value, key) {
            $(`<div class="alert alert-danger">
              ${_.isString(value) ? value : value[0]}
              </div>`
            ).appendTo(inner)
          })
        })
        .finally(() => {
          inner.appendTo(busca_render)
        })
    })

    busca_despesa.keyup((event) => {
      if (event.target.value === '') {
        add_registro[0].data = null
        form.find('input[name^="despesa_"]').attr('readonly', false)
        busca_render.html('')
        return
      }
      axios.get(`/api/loa/despesaconsulta/search/?page_size=5&ano=${ano_loa}&q=${event.target.value}`)
        .then((response) => {
          busca_render.html('')
          const inner = $('<div class="inner"></div>')
          inner.appendTo(busca_render)
          if (_.isEmpty(response.data.results)) {
            add_registro[0].data = null
            form.find('input[name^="despesa_"]').attr('readonly', false)
            $(`<div class="alert alert-warning">
              Nenhuma despesa encontrada nos anexos da LOA com esta informação. Você pode ainda fazer o registro manualmente no formulário acima.
            </div>`).appendTo(inner)
          }
          let parts = event.target.value.trim().split(' ')

          _.each(response.data.results, (value, idx) => {
            let html = `<div class="small item hover_background_05p" pk="${value.id}">
                Órgão: ${value.cod_orgao} - ${value.esp_orgao}<br>
                Und Orç: ${value.cod_unidade} - ${value.esp_unidade}<br>
                Código: ${value.codigo} - ${value.especificacao}<br>
                Natureza: ${value.cod_natureza}
              </div>`

            _.each(parts, (p, idx) => {
              html = html.replaceAll(p.toUpperCase(), `<strong class="text-blue">${p.toUpperCase()}</strong>`)
            })

            let item = $(html).appendTo(inner)

            item.click((event) => {
              form.find('input[name="despesa_codigo"]').val(value.codigo)
              form.find('input[name="despesa_unidade"]').val(value.cod_unidade)
              form.find('input[name="despesa_especificacao"]').val(value.especificacao)
              form.find('input[name="despesa_natureza"]').val(value.cod_natureza)

              form.find('input[name^="despesa_"]').attr('readonly', true)
              let pk_despesa = event.currentTarget.getAttribute('pk')

              add_registro[0].data = pk_despesa
              busca_render.html('')
            })
          })
        })
        .catch(() => {
        })
    })

    form.keydown((event) => {
      if (event.keyCode === 13) {
        event.preventDefault()
        return false
      }
    })

    form.change(function (event) {
      let formData = {}
      let field = event.target.name
      let value = event.target.value

      let action = '/'

      preview.style.opacity = 0.35

      let parlamentar_id = event.target.getAttribute('parlamentar_id')
      if (parlamentar_id !== null) {
        formData['valor'] = value
        formData['parlamentar_id'] = parlamentar_id
        action = '/updatevalorparlamentar/'
      } else if (field === 'lineHeight') {
        preview.src = `${urlBase}/preview/?page=1&lineHeight=${value}&u=${Date.now()}`
        return
      } else {
        formData[field] = value
      }

      axios.patch(`${urlBase}${action}`, formData)
        .then((response) => {
          form.find('input[name="lineHeight"]').val(response.data.metadata.style.lineHeight)
          form.find('input[name="valor"]').val(response.data.valor)
          preview.src = `${urlBase}/preview/?page=1&u=${Date.now()}`
        })
        .catch(() => {
        })
    })
    form.trigger('change')
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
