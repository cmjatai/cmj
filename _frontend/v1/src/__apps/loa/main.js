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
    const formData = new FormData(form[0])
    const formProps = Object.fromEntries(formData)
    const formJson = JSON.stringify(formProps)

    if (formJson === '{}') {
      const lsJson = localStorage.getItem('portalcmj_emendaloa_filter')
      const lsData = JSON.parse(lsJson)

      if (lsJson !== '{}') {
        _.forOwn(lsData, (value, key) => {
          console.log(lsData)
          _.forEach(form.find(`input[name="${key}"]`), (item) => {
            if ((Array.isArray(value) && value.includes(item.value)) || value === item.value) {
              item.checked = true
              $(`label[for="${item.id}"] span`).addClass('active')
            }
          })
        })
        form.submit()
      }
    } else {
      localStorage.setItem('portalcmj_emendaloa_filter', formJson)
    }
    form
      .find('input[type="checkbox"]')
      .change((event) => {
        const formData = new FormData(form[0])
        const parlamentares = formData.getAll('parlamentares')
        const fase = formData.getAll('fase')
        const tipo = formData.getAll('tipo')
        const formProps = tipo.length > 0 || fase.length > 0 || parlamentares.length > 0 ? { fase, parlamentares, tipo } : {}
        const formJson = JSON.stringify(formProps)
        localStorage.setItem('portalcmj_emendaloa_filter', formJson)

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
            let text_html = `
                Órgão...: ${value.cod_orgao} - ${value.esp_orgao}<br>
                Und Orç.: ${value.cod_unidade} - ${value.esp_unidade}<br>
                Código..: ${value.codigo} - ${value.especificacao}<br>
                Natureza: ${value.cod_natureza} - ${value.esp_natureza}<br>
                Val.Orç.: ${value.str_valor} | Saldo: ${value.str_saldo}`

            _.each(parts, (p, idx) => {
              text_html = text_html.replaceAll(p.toUpperCase(), `<strong class="text-blue">${p.toUpperCase()}</strong>`)
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
          // $('.decimalinput').mask('###.###.##0,00', { reverse: true })
          refreshChangeRegistroDespesa()

          preview.src = `${urlBase}/view/?page=1&u=${Date.now()}`
        })
        .catch((event) => {
          // console.log(event)
        })
    })
    form.trigger('change')
  }
  instance.AgrupamentoCRUD = function () {
    const container = $('.container-loa')
    if (container.hasClass('agrupamento-update')) {
      instance.AgrupamentoCrudUPDATE(container)
    }
  }
  instance.AgrupamentoCrudUPDATE = function (container) {
    const pk = window.location.href.matchAll(/agrupamento\/(\d+)\//g).next().value[1]
    const form = container.find('form')
    const urlBase = `/api/loa/agrupamento/${pk}`

    const rcs = form.find('.registro-render')
    const createRegistroRender = function () {
      rcs.html('')
      $('<div class="inner"></div>').appendTo(rcs)
      $('<div class="footer"></div>').appendTo(rcs)
    }
    createRegistroRender()

    const refreshChangeRegistroDespesa = function () {
      const inner = rcs.find('.inner')
      // const footer = rcs.find('.footer')

      axios.get(`/api/loa/agrupamentoregistrocontabil/?agrupamento=${pk}&get_all=true`)
        .then((response) => {
          _.each(response.data, (value, idx) => {
            if (inner.find(`.item-rc[pk="${value.id}"]`).length > 0) {
              return
            }
            const item = $(`<div class="item-rc" pk="${value.id}"></div>`)
            item.appendTo(inner)

            let texto = value.__str__
            let pos = texto.search(/(\d)%/g)
            let i = 0
            while (pos > 0 && pos < 6 && i < 10) {
              texto = ' ' + texto
              pos = texto.search(/(\d)%/g)
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
                axios.delete(`/api/loa/agrupamentoregistrocontabil/${pk}/`)
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
      formData.agrupamento = pk
      formData.despesa = pk_despesa
      formData.codigo = form.find('input[name="despesa_codigo"]').val()
      formData.orgao = form.find('input[name="despesa_orgao"]').val()
      formData.unidade = form.find('input[name="despesa_unidade"]').val()
      formData.especificacao = form.find('input[name="despesa_especificacao"]').val()
      formData.natureza = form.find('input[name="despesa_natureza"]').val()
      formData.percentual = form.find('input[name="perc_despesa"]').val()
      busca_render.html('')
      const inner = $('<div class="inner"></div>')
      axios.post(`/api/loa/agrupamentoregistrocontabil/create_for_agrupamento_update/`, formData)
        .then((response) => {
          add_registro[0].data = null
          form.find('input[name^="despesa_"], input[name$="_despesa"]')
            .val('')
            .attr('readonly', false)
            .removeClass('is-invalid')
          form.find('input[name="perc_despesa"]').val('100,00')

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
      form.find('input[name^="despesa_"], input[name$="_despesa"]').removeClass('is-invalid')
      if (event.target.value.trim() === '') {
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
            let text_html = `
                Órgão...: ${value.cod_orgao} - ${value.esp_orgao}<br>
                Und Orç.: ${value.cod_unidade} - ${value.esp_unidade}<br>
                Código..: ${value.codigo} - ${value.especificacao}<br>
                Natureza: ${value.cod_natureza} - ${value.esp_natureza}<br>
                Val.Orç.: ${value.str_valor} | Saldo: ${value.str_saldo}`

            _.each(parts, (p, idx) => {
              text_html = text_html.replaceAll(p.toUpperCase(), `<strong class="text-blue">${p.toUpperCase()}</strong>`)
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

    const emendaloa_selecteds = form.find('.emendaloa-selecteds')
    const busca_render_emendaloa = form.find('.busca-render-emendaloa')
    const busca_emendaloa = form.find('input[name="busca_emendaloa"]')

    const refreshChangeRegistroAgrupamento = function () {
      axios.get(`/api/loa/agrupamento/${pk}/emendas/?&get_all=true`)
        .then((response) => {
          emendaloa_selecteds.html('')
          const inner = $('<div class="inner"></div>')
          inner.appendTo(emendaloa_selecteds)

          _.each(response.data, (value, idx) => {
            const inner_item = $('<div class="inner-item"></div>').appendTo(inner)

            $(
              `<div class="item-emendaloa" pk="${value.id}">
              <strong>Valor da Emenda Impositiva: R$ ${value.str_valor}</strong><br>
              <strong>${value.indicacao}</strong><br>
              <a href="${value.link_detail_backend}/edit" target="_blank">${value.finalidade}</a><br>
              ${value.str_parlamentares.join('<br>')}
              <span class="fase ${value.fase === 10 ? 'bg-danger' : value.fase === 12 ? 'bg-warning' : 'bg-green'}">${value.str_fase}</span>
              </div>`
            ).appendTo(inner_item)

            const inner_actions = $('<div class="inner-actions"></div>').appendTo(inner_item)
            $(
              `<span class="btn btn-delete text-danger" pk="${value.id}" title="Remover Emenda do Agrupamento."><i class="far fa-trash-alt"></i></span>`
            ).appendTo(inner_actions).click((event) => {
              let pk_emendaloa = event.currentTarget.getAttribute('pk')
              let formData = {}
              formData.agrupamento = pk
              formData.emendaloa = pk_emendaloa
              axios.post(`/api/loa/agrupamentoemendaloa/delete/`, formData)
                .then((response) => {
                  refreshChangeRegistroAgrupamento()
                })
                .catch((error) => {
                  busca_render_emendaloa.find('.alert').remove()
                  inner.prepend($(`<div class="alert alert-danger">
                    ${error.message}
                    </div>`
                  ))
                })
            })
          })
        })
    }
    refreshChangeRegistroAgrupamento()

    busca_emendaloa.keyup((event) => {
      if (event.ctrlKey) {
        return
      }
      if (event.target.value.trim() === '') {
        busca_render_emendaloa.html('')
        return
      }
      if (event.target.value.trim().length < 3) {
        busca_render_emendaloa.html('Digite ao menos três letras')
        return
      }
      axios.get(`/api/loa/emendaloa/search/?&get_all=true&ano=${ano_loa}&q=${event.target.value}`)
        .then((response) => {
          busca_render_emendaloa.html('')
          const inner = $('<div class="inner"></div>')

          inner.appendTo(busca_render_emendaloa)

          _.each(response.data, (value, idx) => {
            if (emendaloa_selecteds.find(`.item-emendaloa[pk="${value.id}"]`).length > 0) {
              return
            }
            const inner_item = $('<div class="inner-item"></div>').appendTo(inner)

            $(`<div class="item-emendaloa" pk="${value.id}">
                <strong>Valor da Emenda Impositiva: R$ ${value.str_valor}</strong><br>
                <strong>${value.indicacao}</strong><br>
                <a href="${value.link_detail_backend}/edit" target="_blank">${value.finalidade}</a><br>
                ${value.str_parlamentares.join('<br>')}<br>
                <span class="fase ${value.fase === 10 ? 'bg-danger' : value.fase === 12 ? 'bg-warning' : 'bg-green'}">${value.str_fase}</span>
              </div>`).appendTo(inner_item)

            if (value.fase === 10) {
              return
            }

            const inner_actions = $('<div class="inner-actions"></div>').appendTo(inner_item)
            $(
              `<span class="btn text-blue" pk="${value.id}" title="Adicionar Emenda ao Agrupamento."><i class="far fa-arrow-alt-circle-right"></i></i></span>`
            ).appendTo(inner_actions).click((event) => {
              let pk_emendaloa = event.currentTarget.getAttribute('pk')
              let formData = {}
              formData.agrupamento = pk
              formData.emendaloa = pk_emendaloa
              formData.emendaloa__fase = 15
              axios.post(`/api/loa/agrupamentoemendaloa/`, formData)
                .then((response) => {
                  busca_render_emendaloa.find(`.item-emendaloa[pk="${response.data.emendaloa}"]`).parent().remove()
                  refreshChangeRegistroAgrupamento()
                })
                .catch((error) => {
                  busca_render_emendaloa.find('.alert').remove()
                  inner.prepend($(`<div class="pt-2"><div class="alert alert-danger">
                    ${error.response.data[0]}
                    </div></div>`
                  ))
                })
            })
          })
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

      formData[field] = value

      axios.patch(`${urlBase}${action}`, formData)
        .then((response) => {
          // $('.decimalinput').mask('###.###.##0,00', { reverse: true })
          refreshChangeRegistroDespesa()

          // preview.src = `${urlBase}/view/?page=1&u=${Date.now()}`
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
    instance.AgrupamentoCRUD()
  }
  instance.init()
}

$(document).ready(function () {
  if ($('.container-loa').length > 0) {
    window.AppLOA()
  }
})
