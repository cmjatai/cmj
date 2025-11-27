import EmendaLoaForm from './EmendaLoaForm'
import axios from 'axios'

export default class EmendaLoaUpdate extends EmendaLoaForm {
  constructor (container) {
    super(container)
    this.init()
  }

  async init () {
    // const container = this.container
    const pk = window.location.href.matchAll(/emendaloa\/(\d+)\//g).next().value[1]
    const form = this.form
    const urlBase = `/api/loa/emendaloa/${pk}`

    let pkObject = null
    const pkObjectRefresh = async function () {
      return axios.get(`${urlBase}/`)
        .then((response) => {
          pkObject = response.data
        })
    }
    await pkObjectRefresh()

    this.toggleTipo()

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
                name="lineHeight" value="${pkObject.metadata.style.lineHeight}"
                step="5"
                min="100"
                max="350"
                class="numberinput form-control text-center"
                id="id_lineHeight">
            </label>
          </div>
          <div>
            <label for="id_espacoAssinatura">
            <input type="checkbox"
              ${pkObject.metadata.style.espacoAssinatura ? 'checked' : ''}
              name="espacoAssinatura"
              class="form-check-input"
              id="id_espacoAssinatura">
            <span>Incluir espaço para Assinaturas</span>
            </label>
          </div>
        </div>
      `)
    }
    const preview = createPreview().find('img')[0]
    preview.onload = function (event) {
      preview.style.opacity = 1
      pkObjectRefresh()
    }

    const rcs = form.find('.registro-render')
    const createRegistroRender = function () {
      rcs.html('')
      $('<div class="inner"></div>').appendTo(rcs)
      $('<div class="footer"></div>').appendTo(rcs)
    }
    createRegistroRender()

    const refreshChangeRegistroDespesa = function (clear_render_list = false) {
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
          if (clear_render_list) {
            inner.html('')
          }
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
                    preview.src = `${urlBase}/view/?page=1&u=${Date.now()}`
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
              })
          })
        })
    }
    refreshChangeRegistroDespesa()

    const ano_loa = form.find('input[name="ano_loa"')[0].value
    const busca_render = form.find('.busca-render')
    const busca_despesa = form.find('input[name="busca_despesa"]')

    const add_registro = form.find('#add_registro')

    const clean_form_search = form.find('#clean_form_search')
    clean_form_search.click((event) => {
      add_registro[0].data = null
      form.find('input[name^="despesa_"], input[name$="_despesa"]')
        .val('')
        .attr('readonly', false)
        .removeClass('is-invalid')
    })
    add_registro.click((event) => {
      let pk_despesa = add_registro[0].data
      console.debug(pk_despesa)
      let formData = {}
      formData.emendaloa = pk
      formData.despesa = pk_despesa
      formData.codigo = form.find('input[name="despesa_codigo"]').val()
      formData.orgao = form.find('input[name="despesa_orgao"]').val()
      formData.unidade = form.find('input[name="despesa_unidade"]').val()
      formData.especificacao = form.find('input[name="despesa_especificacao"]').val()
      formData.natureza = form.find('input[name="despesa_natureza"]').val()
      formData.fonte = form.find('input[name="despesa_fonte"]').val()
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
          preview.src = `${urlBase}/view/?page=1&u=${Date.now()}`

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
      axios.get(`/api/loa/despesaconsulta/search/?page_size=10&ano=${ano_loa}&q=${event.target.value}`)
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
          } else if (response.data.pagination.total_entries > 10) {
            let msg_rodape = `<div class="alert alert-warning">
              <em>Mostrando 10 primeiros resultados de ${response.data.pagination.total_entries}.<br>Informe mais termos no campo de busca para reduzir os resultados.</em>
            </div>`
            $(msg_rodape).appendTo(inner)
          }

          let parts = event.target.value.trim().split(' ')

          _.each(response.data.results, (value, idx) => {
            let text_html = `
                Órgão...: ${value.cod_orgao} - ${value.esp_orgao}<br>
                Und Orç.: ${value.cod_unidade} - ${value.esp_unidade}<br>
                Código..: ${value.codigo} - ${value.especificacao}<br>
                Natureza: ${value.cod_natureza} - ${value.esp_natureza} // Fonte: ${value.cod_fonte}<br>
                Val.Orç.: ${value.str_valor} | Saldo: ${value.str_saldo}`

            _.each(parts, (p, idx) => {
              const re = new RegExp(`(${p})`, 'ig')
              text_html = text_html.replace(re, '<strong class="highlight">$1</strong>')
            })
            let html = `<div class="small item" pk="${value.id}">
                ${text_html}
              </div>`

            let item = $(html).appendTo(inner)

            item.click((event) => {
              // form.find('input[name="indicacao"]').val(value.esp_unidade).trigger('change')
              form.find('input[name="despesa_codigo"]').val(value.codigo)
              form.find('input[name="despesa_orgao"]').val(value.cod_orgao)
              form.find('input[name="despesa_unidade"]').val(value.cod_unidade)
              form.find('input[name="despesa_especificacao"]').val(value.especificacao)
              form.find('input[name="despesa_natureza"]').val(value.cod_natureza)
              form.find('input[name="despesa_fonte"]').val(value.cod_fonte)

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

      if (field === '') {
        return
      }

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
      } else if (field === 'espacoAssinatura') {
        preview.src = `${urlBase}/view/?page=1&espacoAssinatura=${event.target.checked}&u=${Date.now()}`
        return
      } else if (field === 'parl_assinantes') {
        action = '/update_parlassinantes/'
        formData['parlamentar_id'] = value
        formData['checked'] = event.target.checked
      } else if (field === 'valor') {
        action = '/updatevaloremenda/'
        formData['valor'] = value
      } else {
        formData[field] = value
      }

      axios.patch(`${urlBase}${action}`, formData)
        .then((response) => {
          form.find('input[name="lineHeight"]').val(response.data.metadata.style.lineHeight)
          form.find('input[name="valor"]').val(response.data.valor)
          // $('.decimalinput').mask('###.###.##0,00', { reverse: true })

          if (field === 'tipo') {
            window.location.reload()
          }

          refreshChangeRegistroDespesa(true)

          preview.src = `${urlBase}/view/?page=1&u=${Date.now()}`
        })
        .catch((event) => {
          window.location.reload()
        })
    })
    form.trigger('change')
  }
}
