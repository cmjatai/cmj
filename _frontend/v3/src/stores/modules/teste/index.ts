import Api from '@/api'

export default {
  namespaced: true,

  state: () => ({
    autores: {}
  }),

  actions: {
    async fetchAutores ({ dispatch, commit }, page=1) {
      console.log('action fetch autores')
      await Api.getModelList('base', 'autor', page=page).then(async (data:any) => {
        data.data.results.forEach((m: any) => {
          commit('setAutor', m )            
        });
        if (data.data.pagination.next_page > 0)          {
          await dispatch('fetchAutores', page = data.data.pagination.next_page)
        }
      })
    }
  },

  mutations: {
    setAutor (state, autor) {
      state.autores[autor.id] = autor
    }
  }
}