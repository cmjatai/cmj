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
  instance.LoaCRUD = function () {
    const container = $('.container-loa')
    if (container.hasClass('loa-detail')) {
      instance.LoaCrudDETAIL(container)
    }
  }
  instance.LoaCrudDETAIL = function (container) {}
  instance.EmendaLoaCRUD = function () {
    const container = $('.container-loa')
    if (container.hasClass('emendaloa-update')) {
      instance.EmendaLoaCrudUPDATE(container)
    } else if (container.hasClass('emendaloa-list')) {
      instance.EmendaLoaCrudLIST(container)
    }
  }
  instance.EmendaLoaCrudLIST = function (container) {
    const form = container.find('form')
    form
      .find('input[type="checkbox"]')
      .change((event) => {
        form.submit()
      })
  }
  instance.EmendaLoaCrudUPDATE = function (container) {
    const pk = window.location.href.matchAll(/emendaloa\/(\d+)\//g).next().value[1]
    const form = container.find('form')
    const urlBase = `/api/loa/emendaloa/${pk}`

    const createPreview = function () {
      return $('.container-preview').html(`
        <div class="inner-preview">
          <a class="w-100" target="_blank" href="${urlBase}/view/">
            <img src="${urlBase}/view/?page=1&u=${Date.now()}"/>
          </a>
        </div>
        <div class="btn-toolbar justify-content-between">
          <div class="btn-group btn-group-sm">
            <label for="id_lineHeight">
              <span>Entrelinha (%)</span>
              <input type="number"
                name="lineHeight" value="150"
                step="5"
                min="100"
                max="350"
                class="numberinput form-control text-center"
                id="id_lineHeight">
            </label>
          </div>
        </div>
      `)
    }
    const preview = createPreview().find('img')[0]
    preview.onload = function (event) {
      preview.style.opacity = 1
    }

    const rcs = form.find('.registro-render')
    const createRegistroRender = function () {
      rcs.html('')
      $('<div class="inner"></div>').appendTo(rcs)
      $('<div class="footer"></div>').appendTo(rcs)
    }
    createRegistroRender()

    const refreshChangeRegistroDespesa = function () {
      const inner = rcs.find('.inner')
      const footer = rcs.find('.footer')
      axios.get(`/api/loa/emendaloa/${pk}/totais/`)
        .then((response) => {
          footer.html('')
          $(`
            <div class="row">
              <div class="col-12 totais">
              TOTAIS:
              </div>
              <div class="col">
                <span class="key">Inserções</span>
                <span class="value">${response.data.soma_insercoes}</span>
              </div>
              <div class="col">
                <span class="key">Deduções</span>
                <span class="value">${response.data.soma_deducoes}</span>
              </div>
              <div class="col text-${response.data.divergencia_registros === '0,00' ? 'blue' : 'red'}">
                <span class="key">Inserções + Deduções</span>
                <span class="value">${response.data.divergencia_registros}</span>
              </div>
              <div class="col text-${response.data.divergencia_emenda === '0,00' ? 'blue' : 'red'}">
                <span class="key">Emenda - Inserções</span>
                <span class="value">${response.data.divergencia_emenda}</span>
              </div>
            </div>
            `).appendTo(footer)
        })
      axios.get(`/api/loa/emendaloaregistrocontabil/?emendaloa=${pk}&get_all=true`)
        .then((response) => {
          _.each(response.data, (value, idx) => {
            if (inner.find(`.item-rc[pk="${value.id}"]`).length > 0) {
              return
            }
            const item = $(`<div class="item-rc" pk="${value.id}"></div>`)
            item.appendTo(inner)

            let texto = value.__str__
            let pos = texto.search(/(\d) /g)
            let i = 0
            while (pos > 0 && pos < 15 && i < 20) {
              texto = texto.replace(/^R\$/g, 'R$ ')
              pos = texto.search(/(\d) /g)
              i += 1
            }
            texto = texto.split(' - ')
            texto[0] = `<strong>${texto[0]}</strong>`
            texto = texto.join(' - ')
            texto = texto.replaceAll(' ', '&nbsp;')
            $(`<span class="texto">${texto}</span>`)
              .appendTo(item)

            $(`<span class="btn btn-sm btn-delete text-danger"><i class="far fa-trash-alt"></i></span>`)
              .appendTo(item).click((event) => {
                const pk = event.target.closest('.item-rc').getAttribute('pk')
                axios.delete(`/api/loa/emendaloaregistrocontabil/${pk}/`)
                  .then((response) => {
                    form.trigger('change')
                    event.target.closest('.item-rc').remove()
                    refreshChangeRegistroDespesa()
                  })
              })
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
      formData.orgao = form.find('input[name="despesa_orgao"]').val()
      formData.unidade = form.find('input[name="despesa_unidade"]').val()
      formData.especificacao = form.find('input[name="despesa_especificacao"]').val()
      formData.natureza = form.find('input[name="despesa_natureza"]').val()
      formData.valor = form.find('input[name="valor_despesa"]').val()
      busca_render.html('')
      const inner = $('<div class="inner"></div>')
      axios.post(`/api/loa/emendaloaregistrocontabil/create_for_emendaloa_update/`, formData)
        .then((response) => {
          add_registro[0].data = null
          form.find('input[name^="despesa_"], input[name$="_despesa"]')
            .val('')
            .attr('readonly', false)
            .removeClass('is-invalid')

          $('<div class="alert alert-info>Registro de Despesa Adicionado com sucesso.</div>'
          ).appendTo(inner)

          refreshChangeRegistroDespesa()
          form.trigger('change')
        })
        .catch((error) => {
          if (_.isString(error.response) || _.isString(error.response.data)) {
            $(`<div class="alert alert-danger">
              ${error.message}
              </div>`
            ).appendTo(inner)
            return
          }
          _.forOwn(error.response.data, function (value, key) {
            form.find(`input[name=despesa_${key}], input[name=${key}_despesa]`).addClass('is-invalid')

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
      if (event.target.value.trim() === '') {
        add_registro[0].data = null
        form.find('input[name^="despesa_"]').attr('readonly', false)
        form.find('input[name^="despesa_"], input[name$="_despesa"]').removeClass('is-invalid')
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
            let html = `<div class="small item" pk="${value.id}">
                Órgão...: ${value.cod_orgao} - ${value.esp_orgao}<br>
                Und Orç.: ${value.cod_unidade} - ${value.esp_unidade}<br>
                Código..: ${value.codigo} - ${value.especificacao}<br>
                Natureza: ${value.cod_natureza} - ${value.esp_natureza}
              </div>`

            _.each(parts, (p, idx) => {
              html = html.replaceAll(p.toUpperCase(), `<strong class="text-blue">${p.toUpperCase()}</strong>`)
            })

            let item = $(html).appendTo(inner)

            item.click((event) => {
              form.find('input[name="indicacao"]').val(value.esp_unidade).trigger('change')
              form.find('input[name="despesa_codigo"]').val(value.codigo)
              form.find('input[name="despesa_orgao"]').val(value.cod_orgao)
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

    form.keypress((event) => {
      if (event.keyCode === 13) {
        event.preventDefault()

        if (event.target === busca_despesa[0]) {
          const items = busca_render.find('.inner')
          const children = items.children()
          if (children.length === 1) {
            children.trigger('click')
          }
        }

        return false
      }
    })

    form.find('select[name="fase"]').change((event) => {
      const select = event.target
      if (select.value === '10') {
        select.classList.add('is-invalid')
      } else {
        select.classList.remove('is-invalid')
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
        preview.src = `${urlBase}/view/?page=1&lineHeight=${value}&u=${Date.now()}`
        return
      } else {
        formData[field] = value
      }

      axios.patch(`${urlBase}${action}`, formData)
        .then((response) => {
          form.find('input[name="lineHeight"]').val(response.data.metadata.style.lineHeight)
          form.find('input[name="valor"]').val(response.data.valor)
          refreshChangeRegistroDespesa()

          preview.src = `${urlBase}/view/?page=1&u=${Date.now()}`
        })
        .catch((event) => {
          // console.log(event)
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
