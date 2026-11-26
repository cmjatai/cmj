import $ from 'jquery'
import axios from 'axios'
import _ from 'lodash'
import { mensagemDoErro } from '../mensagens'

// Campos do model Agrupamento que o autosave envia, com o rótulo usado nas mensagens
// (LOA-AGR-063 e LOA-AGR-064)
const CAMPOS_DO_MODEL = {
  nome: 'Nome',
  tipo: 'Área de aplicação',
  finalidade: 'Finalidade'
}

// Mensagem guardada para ser mostrada depois do recarregamento da página (LOA-AGR-090)
const CHAVE_MENSAGEM_GUARDADA = 'agrupamento-mensagem-guardada'

// Tempo até sumirem as mensagens de sucesso e informação (LOA-AGR-090)
const TEMPO_MENSAGEM_MS = 8000

// Fases em que a emenda é devolvida para correção por esta tela (LOA-AGR-091). O servidor
// confere de novo e recusa a coletiva e a emenda de outro agrupamento.
const FASES_DEVOLVIVEIS = [12, 15, 17]

export default class AgrupamentoUpdate {
  constructor (container) {
    this.container = container
    this.form = container.find('form')
    this.pk = window.location.href.matchAll(/agrupamento\/(\d+)\//g).next().value[1]
    this.urlBase = `/api/loa/agrupamento/${this.pk}`
    this.ano_loa = this.form.find('input[name="ano_loa"')[0].value

    this.mensagens = $('<div class="agrupamento-mensagens"></div>').appendTo(this.container)

    this.init()
  }

  // Mensagem suspensa no canto superior direito, no lugar de alert() (LOA-AGR-090).
  // Erros e avisos ficam até serem fechados; sucesso e informação somem sozinhos.
  mostrarMensagem (texto, tipo = 'danger', titulo = '') {
    const chave = `${tipo}\n${titulo}\n${texto}`
    const repetido = this.mensagens.children().toArray()
      .some((el) => el.getAttribute('data-chave') === chave)
    if (repetido) return

    const alerta = $(`
      <div class="alert alert-${tipo} alert-dismissible" role="alert">
        <button type="button" class="close" aria-label="Fechar">
          <span aria-hidden="true">&times;</span>
        </button>
        <strong class="d-block"></strong>
        <span class="texto"></span>
      </div>
    `)
    alerta.attr('data-chave', chave)
    if (titulo) {
      alerta.find('strong').text(titulo)
    } else {
      alerta.find('strong').remove()
    }
    alerta.find('.texto').text(texto).css('white-space', 'pre-line')
    alerta.find('.close').click(() => alerta.remove())
    alerta.appendTo(this.mensagens)

    if (tipo === 'success' || tipo === 'info') {
      setTimeout(() => alerta.remove(), TEMPO_MENSAGEM_MS)
    }
  }

  // Guarda a mensagem e recarrega a página, que a mostra ao abrir
  recarregarComMensagem (texto, tipo = 'success') {
    window.sessionStorage.setItem(
      CHAVE_MENSAGEM_GUARDADA,
      JSON.stringify({ pk: this.pk, texto, tipo })
    )
    window.location.reload()
  }

  mostrarMensagemGuardada () {
    const guardada = window.sessionStorage.getItem(CHAVE_MENSAGEM_GUARDADA)
    if (!guardada) return
    window.sessionStorage.removeItem(CHAVE_MENSAGEM_GUARDADA)
    try {
      const { pk, texto, tipo } = JSON.parse(guardada)
      if (pk === this.pk) this.mostrarMensagem(texto, tipo)
    } catch (e) {}
  }

  // Erros do clean() do formulário, como o bloqueio da liberação (LOA-AGR-082),
  // saem do topo do formulário e vão para a mensagem suspensa
  mostrarErrosDoFormulario () {
    this.form.find('.alert.alert-block.alert-danger').each((i, el) => {
      const itens = $(el).find('li').toArray().map((li) => $(li).text().trim())
      const texto = itens.length > 0 ? itens.join('\n') : $(el).text().trim()
      if (texto) {
        this.mostrarMensagem(texto, 'danger', 'Não foi possível liberar para protocolo.')
      }
      $(el).remove()
    })
  }

  init () {
    this.mostrarMensagemGuardada()
    this.mostrarErrosDoFormulario()
    this.setupRegistroRender()
    this.loadRegistrosContabeis()
    this.setupBuscaDespesa()
    this.setupEmendasAgrupamento()
    this.setupFormEvents()
    this.setupActionsExtras()

    // Trigger initial change to set state
    this.form.trigger('change')
  }

  setupActionsExtras () {
    const create_copia_agrupamento = this.form.find('#create_copia_agrupamento')
    create_copia_agrupamento.click(() => {
      axios.post(`/api/loa/agrupamento/${this.pk}/create_copia/`)
        .then((response) => {
          window.location.href = `/loa/agrupamento/${response.data.pk}/edit`
        })
    })
    const gerar_emenda_coletiva = this.form.find('#gerar_emenda_coletiva')
    gerar_emenda_coletiva.click(() => {
      window.loadingCMJ('Gerando Emendas Coletivas...')
      axios.post(`/api/loa/agrupamento/${this.pk}/gerar_emenda_coletiva/`)
        .then((response) => {
          window.unloadingCMJ()
          if (response.data.status === 'success') {
            if (response.data.emendas_criadas && response.data.emendas_criadas.length === 0) {
              this.mostrarMensagem('Nenhuma emenda coletiva foi criada.', 'warning')
              return
            }
            const n = response.data.emendas_criadas.length
            // a mensagem fica visível alguns segundos antes de ir para o detalhe
            this.mostrarMensagem(
              `${n} emenda(s) coletiva(s) criada(s) com sucesso. Abrindo o detalhe do agrupamento...`,
              'success'
            )
            setTimeout(() => {
              window.location.href = `/loa/agrupamento/${this.pk}`
            }, 3000)
          } else if (response.data.error) {
            this.mostrarMensagem(response.data.error)
          }
        })
        .catch((error) => {
          window.unloadingCMJ()
          this.mostrarMensagem(error.response?.data?.error || 'Ocorreu um erro ao gerar a emenda coletiva.')
        })
    })
    const cancelar_emendas_coletivas = this.form.find('#cancelar_emendas_coletivas')
    cancelar_emendas_coletivas.click(() => {
      // LOA-AGR-072: exclui as coletivas e devolve à edição contábil as emendas em -10 e 17
      if (!confirm(
        'As emendas coletivas geradas serão excluídas, e as emendas do agrupamento que estão ' +
        'transformadas em coletiva ou liberadas (fase 17) voltarão para a edição contábil. Continuar?'
      )) {
        return
      }
      window.loadingCMJ('Cancelando emendas coletivas...')
      axios.post(`/api/loa/agrupamento/${this.pk}/cancelar_emendas_coletivas/`)
        .then((response) => {
          window.unloadingCMJ()
          if (response.data.status === 'success') {
            const { coletivas_excluidas: excluidas, emendas_devolvidas: devolvidas } = response.data
            this.recarregarComMensagem(
              `${excluidas} emenda(s) coletiva(s) excluída(s) e ` +
              `${devolvidas} emenda(s) devolvida(s) para a edição contábil.`
            )
          } else if (response.data.error) {
            this.mostrarMensagem(response.data.error)
          }
        })
        .catch((error) => {
          window.unloadingCMJ()
          this.mostrarMensagem(
            error.response?.data?.error || mensagemDoErro(error),
            'danger',
            'Não foi possível cancelar as emendas coletivas.'
          )
        })
    })
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

    axios.get(`/api/loa/despesaconsulta/search/?page_size=10&ano=${this.ano_loa}&q=${event.target.value}`)
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
              Órgão...: ${value.cod_orgao} - ${value.esp_orgao}
              Und Orç.: ${value.cod_unidade} - ${value.esp_unidade}
              Código..: ${value.codigo} - ${value.especificacao}
              Natureza: ${value.cod_natureza} - ${value.esp_natureza} // Fonte: ${value.cod_fonte}
              Val.Orç.: ${value.str_valor} | Saldo: ${value.str_saldo}`

          _.each(parts, (p) => {
            const re = new RegExp(`(${p})`, 'ig')
            text_html = text_html.replace(re, '<strong class="highlight">$1</strong>')
          })

          text_html = text_html.replaceAll('\n', '<br/>')

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

    this.form.find('#id_finalidade').val('Atualizando...')
    this.carregarFinalidade()

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
              .then((response) => {
                this.form.find('#id_finalidade').val(response.data.agrupamento_finalidade)
                this.loadEmendasAgrupamento()
                this.alertAvisoFinalidade(response.data.aviso_finalidade)
              })
              .catch((error) => {
                busca_render_emendaloa.find('.alert').remove()
                inner.prepend($(`<div class="alert alert-danger">${error.response?.data?.detail || (error.response?.data && error.response?.data[0]) || error.message}</div>`))
              })
          })

          // LOA-AGR-092: a devolvida sai do agrupamento; a lista e a finalidade são recarregadas
          this.botaoDevolver(value, inner_actions, (data) => {
            this.loadEmendasAgrupamento()
            this.alertAvisoFinalidade(data.aviso_finalidade)
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

    let tipo = Number(this.form.find('input[name="tipo"]:checked').val())

    if (tipo >= 0) {
      tipo = `tipo=${tipo}`
    }

    axios.get(`/api/loa/emendaloa/search/?&get_all=true&ano=${this.ano_loa}&q=${parts.join(' ')}&${tipo}`)
      .then((response) => {
        busca_render_emendaloa.html('')
        const inner = $('<div class="inner"></div>')
        inner.appendTo(busca_render_emendaloa)

        _.each(response.data, (value) => {
          if (emendaloa_selecteds.find(`.item-emendaloa[pk="${value.id}"]`).length > 0) {
            return
          }
          if (value.agrupamento && String(value.agrupamento.id) === String(this.pk)) {
            return
          }
          const inner_item = $('<div class="inner-item"></div>').appendTo(inner)

          let text_html = this.renderEmendaItem(value, inner_item, true) // true = return html string

          /* _.each(parts, (p) => {
            const re = new RegExp(`(${p})`, 'ig')
            text_html = text_html.replace(re, '<strong class="highlight">$1</strong>')
          })
          */
          // Replace content with highlighted version
          inner_item.html(text_html)

          // Re-append actions container since we overwrote html
          const inner_actions = $('<div class="inner-actions"></div>').appendTo(inner_item)

          // LOA-AGR-096: a emenda de outro agrupamento é só informação, sem botões; o servidor
          // já a manda para o fim da lista
          if (value.agrupamento) {
            const aviso = $('<small class="agrupamento-da-emenda text-muted">No agrupamento <a target="_blank"></a></small>')
            aviso.find('a').attr('href', value.agrupamento.link_detail_backend).text(value.agrupamento.nome)
            inner_item.find('.item-emendaloa').append(aviso)
            return
          }

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
            this.form.find('#id_finalidade').val('Atualizando...')

            axios.post(`/api/loa/agrupamentoemendaloa/`, formData)
              .then((response) => {
                this.form.find('#id_finalidade').val(response.data.agrupamento_finalidade)
                busca_render_emendaloa.find(`.item-emendaloa[pk="${response.data.emendaloa}"]`).parent().remove()
                this.loadEmendasAgrupamento()
                this.alertAvisoFinalidade(response.data.aviso_finalidade)
              })
              .catch((error) => {
                this.form.find('#id_finalidade').val('')
                busca_render_emendaloa.find('.alert').remove()
                inner.prepend($(`<div class="pt-2"><div class="alert alert-danger">${error.response.data[0]}</div></div>`))
              })
          })

          // LOA-AGR-093: a devolvida sai da busca
          this.botaoDevolver(value, inner_actions, () => inner_item.remove())
        })
      })
  }

  // Botão "Devolver para correção", abaixo da seta e da lixeira (LOA-AGR-091)
  botaoDevolver (value, inner_actions, aoDevolver) {
    if (!FASES_DEVOLVIVEIS.includes(value.fase)) return
    $(
      '<span class="btn btn-devolver text-warning" title="Devolver para correção: a Emenda volta ao autor, na fase Proposta Legislativa."><i class="fas fa-undo-alt"></i></span>'
    ).appendTo(inner_actions).click(() => this.devolverEmenda(value, aoDevolver))
  }

  // Pede confirmação, devolve e mostra a mensagem de sucesso ou o erro (LOA-AGR-093)
  devolverEmenda (value, aoDevolver) {
    const pergunta = `Devolver a Emenda R$ ${value.str_valor} - ${value.indicacao} para correção pelo autor?`
    if (!window.confirm(pergunta)) return Promise.resolve()

    return axios.post(`${this.urlBase}/devolver_emenda/`, { emendaloa: value.id })
      .then((response) => {
        aoDevolver(response.data)
        this.mostrarMensagem(response.data.detail, 'success')
      })
      .catch((error) => {
        this.mostrarMensagem(mensagemDoErro(error), 'danger', 'Não foi possível devolver a Emenda.')
      })
  }

  // Mostra a finalidade gravada no servidor
  carregarFinalidade () {
    return axios.get(`/api/loa/agrupamento/${this.pk}/`)
      .then((response) => {
        this.form.find('#id_finalidade').val(response.data.finalidade || '')
      })
  }

  alertAvisoFinalidade (aviso) {
    // falha da I.A. ou finalidade digitada apagada (LOA-AGR-053): a inclusão/remoção foi feita
    if (aviso) {
      this.mostrarMensagem(aviso, 'warning', 'Finalidade do agrupamento.')
    }
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

    let permite_juncao_coletiva = (value.permite_juncao_coletiva
      ? '<strong class="badge badge-primary" title="Pode ser classificada e permite junção em Emenda Coletiva"><i class="fas fa-check"></i>Permite junção em Emenda Coletiva</strong>'
      : '<strong class="badge badge-warning" title="Pode ser classificada, mas não permite junção coletiva"><i class="fas fa-ban"></i>Não permite junção em Emenda Coletiva</strong>')

    let tipo = value.tipo === 0 ? 'Modificativa' : value.tipo === 10 ? 'Saúde' : 'Geral'
    let text_html = `<div class="item-emendaloa" pk="${value.id}">
      <span class="badge badge-info">Tipo: ${tipo}</span> ${permite_juncao_coletiva}<br>

      <strong>R$ ${value.str_valor}</strong>
        <strong>${value.indicacao}</strong><br>

        <a href="${value.link_detail_backend}/edit" target="_blank">${value.prefixo_finalidade} ${value.finalidade}</a><br>
        <small>${str_parlamentares}</small>
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

    this.form.find('textarea[name="finalidade"]').on('click', (event) => {
      if (!event.ctrlKey) return
      const textarea = this.form.find('textarea[name="finalidade"]')
      textarea.prop('readonly', true)
      textarea.val('Atualizando com I.A...')
      axios.patch(`${this.urlBase}/generate_finalidade_global/`)
        .then((response) => {
          textarea.val(response.data.finalidade_global || '')
          textarea.prop('readonly', false)
        })
        .catch((error) => {
          // o erro vai para a mensagem e o campo volta ao texto gravado, para que o erro
          // não seja gravado como finalidade digitada (LOA-AGR-051 e 053)
          this.mostrarMensagem(
            error.response?.data?.error || error.message,
            'danger',
            'Erro ao gerar a finalidade com I.A.'
          )
          this.carregarFinalidade()
            .finally(() => textarea.prop('readonly', false))
        })
    })

    this.form.change((event) => this.handleAutoSave(event))
  }

  handleAutoSave (event) {
    const field = event.target.name
    const value = event.target.value

    // LOA-AGR-063: buscas, campos despesa_* e perc_despesa não são do model
    if (!_.has(CAMPOS_DO_MODEL, field)) return

    axios.patch(`${this.urlBase}/`, { [field]: value })
      .then(() => {
        this.loadRegistrosContabeis()
      })
      .catch((error) => {
        // LOA-AGR-064: mostra o erro e devolve só este campo ao valor gravado
        this.mostrarMensagem(
          mensagemDoErro(error),
          'danger',
          `Alteração não gravada (${CAMPOS_DO_MODEL[field]}).`
        )
        this.restaurarCampo(field)
      })
  }

  restaurarCampo (field) {
    return axios.get(`${this.urlBase}/`)
      .then((response) => {
        const gravado = response.data[field]
        if (field === 'tipo') {
          this.form.find(`input[name="tipo"][value="${gravado}"]`).prop('checked', true)
        } else {
          this.form.find(`[name="${field}"]`).val(gravado || '')
        }
      })
      .catch((error) => this.mostrarMensagem(
        mensagemDoErro(error),
        'danger',
        'Erro ao recarregar o valor gravado.'
      ))
  }
}
