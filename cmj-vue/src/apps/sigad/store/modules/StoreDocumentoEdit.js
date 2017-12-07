import {
  DOC_OBJECT,
  DOC_TITULO,
  DOC_DESCRICAO
} from '../../mutation-types'

const mutations = {
  [DOC_OBJECT](state, data) {
    if (data && typeof data === 'object') {
      if (data.parent === undefined || data.parent === null) {
        state.documento = data
      }
      else {
        let update_child = parent => {
          if (data.parent === parent.id) {
            parent.childs[data.id] = data
            return true
          }
          for (let child in parent.childs) {
            if (update_child(parent.childs[child]))
              return true
          }
        }
        update_child(state.documento)
      }
    }
  },
  [DOC_TITULO](state, data) {
    if (data && typeof data === 'object') {

      if (state.documento.pk === data.pk) {
        state.documento.titulo = data.titulo
      }

    }
  },

  [DOC_DESCRICAO](state, data) {
    if (data && typeof data === 'object') {
      if (state.documento.pk === data.pk) {
        state.documento.descricao = data.descricao
      }

    }
  },
}

const state = {
  documento: {}
}

const getters = {
  getDocObject: (state, id) => {
    return state.documento
  },
  getChilds: state => state.documento.childs,
  getChoices: state => state.documento.choices,
  getSlug: state => state.documento.slug
}
const actions = {
  setDocObject: ({ commit }, data) => commit(DOC_OBJECT, data),
  setTitulo: ({ commit }, data) => commit(DOC_TITULO, data),
  setDescricao: ({ commit }, data) => commit(DOC_DESCRICAO, data),
}

export default {
  state,
  mutations,
  getters,
  actions,
}
