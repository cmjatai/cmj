import axios from 'axios'
const basePath = '/api'

axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'

export default {
  Utils: {
    getYearsChoiceList: (app, model) => axios({
      url: `${basePath}/${app}/${model}/years/`,
      method: 'GET'
    }),
    getModelOrderedList: (app, model, ordering = '', page = 1, query_string = '') => axios({
      url: `${basePath}/${app}/${model}/?o=${ordering}&page=${page}${query_string}`,
      method: 'GET'
    }),
    getModelList: (app, model, page = 1, query_string = '') => axios({
      url: `${basePath}/${app}/${model}/?page=${page}${query_string}`,
      method: 'GET'
    }),
    getModel: (app, model, id) => axios({
      url: `${basePath}/${app}/${model}/${id}/`,
      method: 'GET'
    }),
    getModelAction: (app, model, id, action) => axios({
      url: `${basePath}/${app}/${model}/${id}/${action}/`,
      method: 'GET'
    }),
    getModelListAction: (app, model, action, page = 1) => axios({
      url: `${basePath}/${app}/${model}/${action}/?page=${page}`,
      method: 'GET'
    }),
    getByMetadata: (m, query_string = '') => axios({
      url: `${basePath}/${m.app}/${m.model}/${m.id}${m.id !== '' ? '/' : ''}${m.action}${m.action !== '' ? '/' : ''}${query_string !== '' ? '?' : ''}${query_string}`,
      method: 'GET'
    })
  }
}
