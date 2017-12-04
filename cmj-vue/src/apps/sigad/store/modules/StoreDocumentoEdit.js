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
        let childs = state.documento.childs
        let update_child = nodeList => {
          let node = nodeList[data.id]
          if (node === undefined) {
            for (let child in nodeList) {
              if (update_child(child.childs))
                break
            }
          }
          else {
            nodeList[data.id] = data
            return true
          }
        }
        update_child(childs)
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
  getDocObject: state => state.documento,
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
