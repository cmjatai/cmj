import EmpenhoForm from './EmpenhoForm'
import axios from 'axios'
// import _ from 'lodash'
import $ from 'jquery'

export default class EmpenhoUpdate extends EmpenhoForm {
  constructor (container) {
    super(container)
    this.pk = window.location.href.matchAll(/empenho\/(\d+)\//g).next().value[1]
    this.urlBase = `/api/loa/empenho/${this.pk}`
    this.pkObject = null
    this.inputBuscas = $('#id_busca_emendas_ajustes')
    this.containerListaBusca = null
    this.containerListaCadastrados = null
    this.containerListas = null

    this.emendasCadastradas = []
    this.ajustesCadastrados = []
    this._debounceTimer = null

    this.init()
  }

  async init () {
    await this.loadPkObject()
    await this.setupContainers()
    await this.fetchEmendasEajustesCadastrados()
    await this.renderEmendasEajustesCadastrados()
    console.debug('Dados do empenho carregados:', this.pkObject)
  }

  async loadPkObject () {
    try {
      const response = await axios.get(`${this.urlBase}/`)
      this.pkObject = response.data
    } catch (error) {
      console.error('Erro ao carregar dados do empenho:', error)
    }
  }

  async createContainerListas () {
    const containerListas = $(`<div class="container-listas d-flex row pt-2"></div>`)
    const containerListaBusca = $(`<div class="col-md-5 container-lista-busca"><h3>Resultados da Busca</h3><div class="lista-busca"></div></div>`)
    const containerListaCadastrados = $(`<div class="col-md-7 container-lista-cadastrados"><h3>Emendas e Ajustes Cadastrados</h3><div class="lista-cadastrados"></div></div>`)
    containerListas.append(containerListaBusca, containerListaCadastrados)
    return containerListas
  }

  async setupContainers () {
    this.createContainerListas().then(container => {
      this.containerListas = container
      // localizar o pai imediato de inputBuscas e adicionar o container no final do mesmo
      this.inputBuscas.parent().append(container)
      this.containerListaCadastrados = container.find('.container-lista-cadastrados')
      this.containerListaBusca = container.find('.container-lista-busca')
    })

    // Configura eventos de busca para emendas e ajustes
    this.inputBuscas.on('input', () => {
      clearTimeout(this._debounceTimer)
      const query = this.inputBuscas.val().trim()
      if (!query) {
        this.containerListaBusca.find('.lista-busca').empty()
        return
      }
      this._debounceTimer = setTimeout(() => this.handleBusca(query), 400)
    })
  }

  async fetchEmendasEajustesCadastrados () {
    try {
      const response = await axios.get(`/api/loa/empenhoemendaajuste/?empenho=${this.pk}&get_all=True&expand=emendaloa,ajuste`)
      this.emendasCadastradas = response.data.filter(item => item.emendaloa?.__label__ === 'loa_emendaloa')
      this.ajustesCadastrados = response.data.filter(item => item.ajuste?.__label__ === 'loa_registroajusteloa')
      console.debug('Emendas cadastradas:', this.emendasCadastradas)
      console.debug('Ajustes cadastrados:', this.ajustesCadastrados)
      return response.data
    } catch (error) {
      console.error('Erro ao carregar emendas e ajustes cadastrados:', error)
      return []
    }
  }
  async renderEmendasEajustesCadastrados () {
    this.containerListaCadastrados.find('.lista-cadastrados').empty()

    if (this.emendasCadastradas.length === 0 && this.ajustesCadastrados.length === 0) {
      this.containerListaCadastrados.find('.lista-cadastrados').append('<p class="text-muted mt-2">Nenhuma emenda ou ajuste cadastrado para este empenho.</p>')
      return
    }

    if (this.emendasCadastradas.length > 0) {
      const secaoEmendas = $('<div class="mt-2"></div>')
      secaoEmendas.append('<h5 class="mb-1"><span class="badge badge-primary">Emendas</span></h5>')
      const ulEmendas = $('<ul class="list-group list-group-flush mb-3"></ul>')
      this.emendasCadastradas.forEach(item => {
        const emenda = item.emendaloa
        const li = $(`
          <li class="list-group-item d-flex justify-content-between align-items-center item-ea" pk="${item.id}">
            <span class="texto-item">
              <span class="badge badge-secondary mr-1">Emenda</span>
              <a href="${emenda.link_detail_backend}" target="_blank" rel="noopener noreferrer">${emenda.epigrafe_short}</a>
              - ${emenda.ementa_format}
            </span>
            <span class="btn btn-sm btn-delete text-danger ml-2" title="Remover vínculo"><i class="far fa-trash-alt"></i></span>
          </li>`)
        li.find('.btn-delete').click(() => this.handleDeleteEmendaAjuste(item.id))
        ulEmendas.append(li)
      })
      secaoEmendas.append(ulEmendas)
      this.containerListaCadastrados.find('.lista-cadastrados').append(secaoEmendas)
    }

    if (this.ajustesCadastrados.length > 0) {
      const secaoAjustes = $('<div class="mt-2"></div>')
      secaoAjustes.append('<h5 class="mb-1"><span class="badge badge-warning">Ajustes</span></h5>')
      const ulAjustes = $('<ul class="list-group list-group-flush mb-3"></ul>')
      this.ajustesCadastrados.forEach(item => {
        const ajuste = item.ajuste
        const li = $(`
          <li class="list-group-item d-flex justify-content-between align-items-center item-ea" pk="${item.id}">
            <span class="texto-item">
              <span class="badge badge-info mr-1">Ajuste</span>
              <a href="${ajuste.link_detail_backend}" target="_blank" rel="noopener noreferrer">${ajuste.__str__}</a>
              - ${ajuste.descricao}
            </span>
            <span class="btn btn-sm btn-delete text-danger ml-2" title="Remover vínculo"><i class="far fa-trash-alt"></i></span>
          </li>`)
        li.find('.btn-delete').click(() => this.handleDeleteEmendaAjuste(item.id))
        ulAjustes.append(li)
      })
      secaoAjustes.append(ulAjustes)
      this.containerListaCadastrados.find('.lista-cadastrados').append(secaoAjustes)
    }
  }

  async handleDeleteEmendaAjuste (pk) {
    try {
      await axios.delete(`/api/loa/empenhoemendaajuste/${pk}/`)
      await this.fetchEmendasEajustesCadastrados()
      await this.renderEmendasEajustesCadastrados()
      const query = this.inputBuscas.val().trim()
      if (query) {
        const { emendas, ajustes } = await this.fetchBusca(query)
        this.renderResultadosBusca(emendas, ajustes)
      }
    } catch (error) {
      console.error('Erro ao remover vínculo:', error)
    }
  }

  async handleBusca (query) {
    const listaBusca = this.containerListaBusca.find('.lista-busca')
    listaBusca.html('<p class="text-muted mt-2"><em>Buscando...</em></p>')
    const { emendas, ajustes } = await this.fetchBusca(query)
    this.renderResultadosBusca(emendas, ajustes)
  }

  async fetchBusca (query) {
    try {
      const [resEmendas, resAjustes] = await Promise.all([
        axios.get(`/api/loa/emendaloa/?search=${encodeURIComponent(query)}`),
        axios.get(`/api/loa/registroajusteloa/?search=${encodeURIComponent(query)}`)
      ])
      return {
        emendas: resEmendas.data.results ?? resEmendas.data.results,
        ajustes: resAjustes.data.results ?? resAjustes.data.results
      }
    } catch (error) {
      console.error('Erro ao buscar emendas e ajustes:', error)
      return { emendas: [], ajustes: [] }
    }
  }

  renderResultadosBusca (emendas, ajustes) {
    const listaBusca = this.containerListaBusca.find('.lista-busca')
    listaBusca.empty()

    if (emendas.length === 0 && ajustes.length === 0) {
      listaBusca.append('<p class="text-muted mt-2">Nenhum resultado encontrado.</p>')
      return
    }

    if (emendas.length > 0) {
      const secao = $('<div class="mt-2"></div>')
      secao.append('<h5 class="mb-1"><span class="badge badge-primary">Emendas</span></h5>')
      const ul = $('<ul class="list-group list-group-flush mb-3"></ul>')
      emendas.forEach(emenda => {
        const jaCadastrado = this.emendasCadastradas.some(ea => ea.emendaloa?.id === emenda.id)
        const li = $(`
          <li class="list-group-item d-flex justify-content-between align-items-center">
            <span class="texto-item">
              <span class="badge badge-secondary mr-1">Emenda</span>
              <a href="${emenda.link_detail_backend}" target="_blank" rel="noopener noreferrer">${emenda.epigrafe_short}</a>
              - ${emenda.ementa_format}
            </span>
            ${jaCadastrado
    ? '<span class="btn btn-sm text-muted ml-2 disabled" title="Já vinculado"><i class="fas fa-check-circle"></i></span>'
    : '<span class="btn btn-sm btn-add text-success ml-2" title="Adicionar vínculo"><i class="fas fa-plus-circle"></i></span>'
}
          </li>`)
        if (!jaCadastrado) {
          li.find('.btn-add').click(() => this.handleAddEmendaAjuste(emenda.id, 'emendaloa'))
        }
        ul.append(li)
      })
      secao.append(ul)
      listaBusca.append(secao)
    }

    if (ajustes.length > 0) {
      const secao = $('<div class="mt-2"></div>')
      secao.append('<h5 class="mb-1"><span class="badge badge-warning">Ajustes</span></h5>')
      const ul = $('<ul class="list-group list-group-flush mb-3"></ul>')
      ajustes.forEach(ajuste => {
        const jaCadastrado = this.ajustesCadastrados.some(ea => ea.ajuste?.id === ajuste.id)
        const li = $(`
          <li class="list-group-item d-flex justify-content-between align-items-center">
            <span class="texto-item">
              <span class="badge badge-info mr-1">Ajuste</span>
              <a href="${ajuste.link_detail_backend}" target="_blank" rel="noopener noreferrer">${ajuste.__str__}</a>
              ${ajuste.descricao ? `- ${ajuste.descricao}` : ''}
            </span>
            ${jaCadastrado
    ? '<span class="btn btn-sm text-muted ml-2 disabled" title="Já vinculado"><i class="fas fa-check-circle"></i></span>'
    : '<span class="btn btn-sm btn-add text-success ml-2" title="Adicionar vínculo"><i class="fas fa-plus-circle"></i></span>'
}
          </li>`)
        if (!jaCadastrado) {
          li.find('.btn-add').click(() => this.handleAddEmendaAjuste(ajuste.id, 'ajuste'))
        }
        ul.append(li)
      })
      secao.append(ul)
      listaBusca.append(secao)
    }
  }

  async handleAddEmendaAjuste (id, tipo) {
    try {
      const payload = { empenho: this.pk, [tipo]: id }
      await axios.post('/api/loa/empenhoemendaajuste/', payload)
      await this.fetchEmendasEajustesCadastrados()
      await this.renderEmendasEajustesCadastrados()
      const query = this.inputBuscas.val().trim()
      if (query) {
        const { emendas, ajustes } = await this.fetchBusca(query)
        this.renderResultadosBusca(emendas, ajustes)
      }
    } catch (error) {
      console.error('Erro ao adicionar vínculo:', error)
    }
  }
}
