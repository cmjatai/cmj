import $ from 'jquery'
import axios from 'axios'
import _ from 'lodash'

export default class AgrupamentoUpdate {
  constructor (container) {
    this.container = container
    this.form = container.find('form')
    this.pk = window.location.href.matchAll(/agrupamento\/(\d+)\//g).next().value[1]
    this.urlBase = `/api/loa/agrupamento/${this.pk}`
    this.ano_loa = this.form.find('input[name="ano_loa"')[0].value

    this.init()
  }

  init () {
    this.setupRegistroRender()
    this.loadRegistrosContabeis()
    this.setupBuscaDespesa()
    this.setupEmendasAgrupamento()
    this.setupFormEvents()

    // Trigger initial change to set state
    this.form.trigger('change')
  }

  setupRegistroRender () {
    const rcs = this.form.find('.registro-render')
    rcs.html('')
    $('<div class="inner"></div>').appendTo(rcs)
    $('<div class="footer"></div>').appendTo(rcs)
  }

  loadRegistrosContabeis () {
    const inner = this.form.find('.registro-render .inner')

    axios.get(`/api/loa/agrupamentoregistrocontabil/?agrupamento=${this.pk}&get_all=true`)
      .then((response) => {
        _.each(response.data, (value) => {
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
          $(`<span class="texto">${texto}</span>`).appendTo(item)

          $(`<span class="btn btn-sm btn-delete text-danger"><i class="far fa-trash-alt"></i></span>`)
            .appendTo(item)
            .click((event) => this.handleDeleteRegistro(event))
        })
      })
  }

  handleDeleteRegistro (event) {
    const pk = event.target.closest('.item-rc').getAttribute('pk')
    axios.delete(`/api/loa/agrupamentoregistrocontabil/${pk}/`)
      .then(() => {
        this.form.trigger('change')
        event.target.closest('.item-rc').remove()
        this.loadRegistrosContabeis()
      })
  }

  setupBuscaDespesa () {
    const busca_render = this.form.find('.busca-render')
    const busca_despesa = this.form.find('input[name="busca_despesa"]')
    const add_registro = this.form.find('#add_registro')
    const clean_form_search = this.form.find('#clean_form_search')

    clean_form_search.click(() => {
      add_registro[0].data = null
      this.form.find('input[name^="despesa_"], input[name$="_despesa"]')
        .val('')
        .attr('readonly', false)
        .removeClass('is-invalid')
    })

    add_registro.click(() => this.handleAddRegistro(add_registro, busca_render))

    busca_despesa.keyup((event) => this.handleBuscaDespesaKeyup(event, add_registro, busca_render))
  }

  handleAddRegistro (add_registro, busca_render) {
    let pk_despesa = add_registro[0].data
    console.debug(pk_despesa)

    let formData = {
      agrupamento: this.pk,
      despesa: pk_despesa,
      codigo: this.form.find('input[name="despesa_codigo"]').val(),
      orgao: this.form.find('input[name="despesa_orgao"]').val(),
      unidade: this.form.find('input[name="despesa_unidade"]').val(),
      especificacao: this.form.find('input[name="despesa_especificacao"]').val(),
      natureza: this.form.find('input[name="despesa_natureza"]').val(),
      fonte: this.form.find('input[name="despesa_fonte"]').val(),
      percentual: this.form.find('input[name="perc_despesa"]').val()
    }

    busca_render.html('')
    const inner = $('<div class="inner"></div>')

    axios.post(`/api/loa/agrupamentoregistrocontabil/create_for_agrupamento_update/`, formData)
      .then(() => {
        add_registro[0].data = null
        this.form.find('input[name^="despesa_"], input[name$="_despesa"]')
          .val('')
          .attr('readonly', false)
          .removeClass('is-invalid')
        this.form.find('input[name="perc_despesa"]').val('100,00')

        $('<div class="alert alert-info>Registro de Despesa Adicionado com sucesso.</div>').appendTo(inner)

        this.loadRegistrosContabeis()
        this.form.trigger('change')
      })
      .catch((error) => {
        if (_.isString(error.response) || _.isString(error.response.data)) {
          $(`<div class="alert alert-danger">${error.message}</div>`).appendTo(inner)
          return
        }
        _.forOwn(error.response.data, (value, key) => {
          this.form.find(`input[name=despesa_${key}], input[name=${key}_despesa]`).addClass('is-invalid')
          $(`<div class="alert alert-danger">${_.isString(value) ? value : value[0]}</div>`).appendTo(inner)
        })
      })
      .finally(() => {
        inner.appendTo(busca_render)
      })
  }

  handleBuscaDespesaKeyup (event, add_registro, busca_render) {
    this.form.find('input[name^="despesa_"], input[name$="_despesa"]').removeClass('is-invalid')

    if (event.target.value.trim() === '') {
      add_registro[0].data = null
      this.form.find('input[name^="despesa_"]').attr('readonly', false)
      busca_render.html('')
      return
    }

    axios.get(`/api/loa/despesaconsulta/search/?page_size=5&ano=${this.ano_loa}&q=${event.target.value}`)
      .then((response) => {
        busca_render.html('')
        const inner = $('<div class="inner"></div>')
        inner.appendTo(busca_render)

        if (_.isEmpty(response.data.results)) {
          add_registro[0].data = null
          this.form.find('input[name^="despesa_"]').attr('readonly', false)
          $(`<div class="alert alert-warning">
            Nenhuma despesa encontrada nos anexos da LOA com esta informação. Você pode ainda fazer o registro manualmente no formulário acima.
          </div>`).appendTo(inner)
        }

        let parts = event.target.value.trim().split(' ')

        _.each(response.data.results, (value) => {
          let text_html = `
              Órgão...: ${value.cod_orgao} - ${value.esp_orgao}<br>
              Und Orç.: ${value.cod_unidade} - ${value.esp_unidade}<br>
              Código..: ${value.codigo} - ${value.especificacao}<br>
              Natureza: ${value.cod_natureza} - ${value.esp_natureza} // Fonte: ${value.cod_fonte}<br>
              Val.Orç.: ${value.str_valor} | Saldo: ${value.str_saldo}`

          _.each(parts, (p) => {
            const re = new RegExp(`(${p})`, 'ig')
            text_html = text_html.replace(re, '<strong class="highlight">$1</strong>')
          })

          let html = `<div class="small item" pk="${value.id}">${text_html}</div>`
          let item = $(html).appendTo(inner)

          item.click((event) => {
            this.form.find('input[name="despesa_codigo"]').val(value.codigo)
            this.form.find('input[name="despesa_orgao"]').val(value.cod_orgao)
            this.form.find('input[name="despesa_unidade"]').val(value.cod_unidade)
            this.form.find('input[name="despesa_especificacao"]').val(value.especificacao)
            this.form.find('input[name="despesa_natureza"]').val(value.cod_natureza)
            this.form.find('input[name="despesa_fonte"]').val(value.cod_fonte)

            this.form.find('input[name^="despesa_"]').attr('readonly', true)
            let pk_despesa = event.currentTarget.getAttribute('pk')

            add_registro[0].data = pk_despesa
            busca_render.html('')
          })
        })
      })
  }

  setupEmendasAgrupamento () {
    const busca_emendaloa = this.form.find('input[name="busca_emendaloa"]')

    this.loadEmendasAgrupamento()

    busca_emendaloa.keyup((event) => this.handleBuscaEmendaKeyup(event))
  }

  loadEmendasAgrupamento () {
    const emendaloa_selecteds = this.form.find('.emendaloa-selecteds')
    const busca_render_emendaloa = this.form.find('.busca-render-emendaloa')

    axios.get(`/api/loa/agrupamento/${this.pk}/emendas/?&get_all=true`)
      .then((response) => {
        emendaloa_selecteds.html('')
        const inner = $('<div class="inner"></div>')
        inner.appendTo(emendaloa_selecteds)

        _.each(response.data, (value) => {
          const inner_item = $('<div class="inner-item"></div>').appendTo(inner)
          this.renderEmendaItem(value, inner_item)

          const inner_actions = $('<div class="inner-actions"></div>').appendTo(inner_item)
          $(
            `<span class="btn btn-delete text-danger" pk="${value.id}" title="Remover Emenda do Agrupamento."><i class="far fa-trash-alt"></i></span>`
          ).appendTo(inner_actions).click((event) => {
            let pk_emendaloa = event.currentTarget.getAttribute('pk')
            let formData = {
              agrupamento: this.pk,
              emendaloa: pk_emendaloa
            }
            axios.post(`/api/loa/agrupamentoemendaloa/delete/`, formData)
              .then(() => {
                this.loadEmendasAgrupamento()
              })
              .catch((error) => {
                busca_render_emendaloa.find('.alert').remove()
                inner.prepend($(`<div class="alert alert-danger">${error.message}</div>`))
              })
          })
        })
      })
  }

  handleBuscaEmendaKeyup (event) {
    if (event.ctrlKey) return

    const busca_render_emendaloa = this.form.find('.busca-render-emendaloa')
    const emendaloa_selecteds = this.form.find('.emendaloa-selecteds')

    if (event.target.value.trim() === '') {
      busca_render_emendaloa.html('')
      return
    }
    if (event.target.value.trim().length < 3) {
      busca_render_emendaloa.html('Digite ao menos três letras')
      return
    }

    let parts = event.target.value.trim().split(' ').filter((p) => p.length >= 3)

    axios.get(`/api/loa/emendaloa/search/?&get_all=true&ano=${this.ano_loa}&q=${parts.join(' ')}`)
      .then((response) => {
        busca_render_emendaloa.html('')
        const inner = $('<div class="inner"></div>')
        inner.appendTo(busca_render_emendaloa)

        _.each(response.data, (value) => {
          if (emendaloa_selecteds.find(`.item-emendaloa[pk="${value.id}"]`).length > 0) {
            return
          }
          const inner_item = $('<div class="inner-item"></div>').appendTo(inner)

          let text_html = this.renderEmendaItem(value, inner_item, true) // true = return html string

          _.each(parts, (p) => {
            const re = new RegExp(`(${p})`, 'ig')
            text_html = text_html.replace(re, '<strong class="highlight">$1</strong>')
          })

          // Replace content with highlighted version
          inner_item.html(text_html)

          // Re-append actions container since we overwrote html
          const inner_actions = $('<div class="inner-actions"></div>').appendTo(inner_item)

          if (value.fase === 10) return

          $(
            `<span class="btn text-blue" pk="${value.id}" title="Adicionar Emenda ao Agrupamento."><i class="far fa-arrow-alt-circle-right"></i></i></span>`
          ).appendTo(inner_actions).click((event) => {
            let pk_emendaloa = event.currentTarget.getAttribute('pk')
            let formData = {
              agrupamento: this.pk,
              emendaloa: pk_emendaloa,
              emendaloa__fase: 15
            }
            axios.post(`/api/loa/agrupamentoemendaloa/`, formData)
              .then((response) => {
                busca_render_emendaloa.find(`.item-emendaloa[pk="${response.data.emendaloa}"]`).parent().remove()
                this.loadEmendasAgrupamento()
              })
              .catch((error) => {
                busca_render_emendaloa.find('.alert').remove()
                inner.prepend($(`<div class="pt-2"><div class="alert alert-danger">${error.response.data[0]}</div></div>`))
              })
          })
        })
      })
  }

  renderEmendaItem (value, container, returnHtml = false) {
    let str_parlamentares = []
    if (value.tipo === 0) {
      _.each(value.str_parlamentares, (p) => {
        p = p.split(' - ')
        str_parlamentares.push(p[1])
      })
    } else {
      str_parlamentares = value.str_parlamentares
    }
    str_parlamentares = str_parlamentares.join('<br>')

    let text_html = `<div class="item-emendaloa" pk="${value.id}">
        Valor da Emenda ${value.tipo !== 0 ? 'Impositiva' : 'Modificativa'}: <strong>R$ ${value.str_valor}</strong><br>
        <strong>${value.indicacao}</strong><br>
        <a href="${value.link_detail_backend}/edit" target="_blank">${value.finalidade}</a><br>
        <small>${str_parlamentares}</small><br>
        <span class="fase ${value.fase === 10 ? 'bg-danger' : value.fase === 12 ? 'bg-warning' : 'bg-green'}">${value.str_fase}</span>
      </div>`

    if (returnHtml) return text_html

    $(text_html).appendTo(container)
  }

  setupFormEvents () {
    const busca_despesa = this.form.find('input[name="busca_despesa"]')
    const busca_render = this.form.find('.busca-render')

    this.form.keypress((event) => {
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

    this.form.find('select[name="fase"]').change((event) => {
      const select = event.target
      if (select.value === '10') {
        select.classList.add('is-invalid')
      } else {
        select.classList.remove('is-invalid')
      }
    })

    this.form.change((event) => this.handleAutoSave(event))
  }

  handleAutoSave (event) {
    let formData = {}
    let field = event.target.name
    let value = event.target.value

    if (!field) return

    let action = '/'
    formData[field] = value

    axios.patch(`${this.urlBase}${action}`, formData)
      .then(() => {
        this.loadRegistrosContabeis()
      })
      .catch(() => {
        // console.debug(event)
      })
  }
}
