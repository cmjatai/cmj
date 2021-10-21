import axios from 'axios'
const basePath = '/api'

axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'

const call_axios = function (obj) {
  // console.log(obj)
  return axios(obj)
}
export default {
  Utils: {
    getYearsChoiceList: (app, model) => call_axios({
      url: `${basePath}/${app}/${model}/years/`,
      method: 'GET'
    }),
    getModelOrderedList: (app, model, ordering = '', page = 1, query_string = '') => call_axios({
      url: `${basePath}/${app}/${model}/?o=${ordering}&page=${page}${query_string}`,
      method: 'GET'
    }),
    getModelList: (app, model, page = 1, query_string = '') => call_axios({
      url: `${basePath}/${app}/${model}/?page=${page}${query_string}`,
      method: 'GET'
    }),
    getModel: (app, model, id) => call_axios({
      url: `${basePath}/${app}/${model}/${id}/`,
      method: 'GET'
    }),
    getModelAction: (app, model, id, action) => call_axios({
      url: `${basePath}/${app}/${model}/${id}/${action}/`,
      method: 'GET'
    }),
    getModelListAction: (app, model, action, page = 1) => call_axios({
      url: `${basePath}/${app}/${model}/${action}/?page=${page}`,
      method: 'GET'
    }),
    getByMetadata: (m, query_string = '') => call_axios({
      url: `${basePath}/${m.app}/${m.model}/${m.id}${m.id !== '' ? '/' : ''}${m.action}${m.action !== '' ? '/' : ''}${query_string !== '' ? '?' : ''}${query_string}`,
      method: 'GET'
    })
  },
  DocumentoResource: {
    getDocumentoChoiceList: (tipo, page) => call_axios({
      url: `${basePath}/documento/?page=${page}&tipo=${tipo}`,
      method: 'GET'
    }),
    getDocumento: id => call_axios({
      url: `${basePath}/documento/${id}/`,
      method: 'GET'
    }),
    createDocumento: (data) => call_axios({
      url: `${basePath}/documento/`,
      data: data,
      method: 'POST'
    }),
    putDocumento: (data) => call_axios({
      url: `${basePath}/documento/${data.id}/`,
      data: data,
      method: 'PUT'
    }),
    updateDocumento: (data) => call_axios({
      url: `${basePath}/documento/${data.id}/`,
      data: data,
      method: 'PATCH'
    }),
    uploadFiles: (id, form) => call_axios({
      url: `${basePath}/documento/${id}/`,
      data: form,
      method: 'PATCH'
    }),
    deleteDocumento: (id) => call_axios({
      url: `${basePath}/documento/${id}/`,
      method: 'DELETE'
    }),
    deleteReferencia: (data) => call_axios({
      url: `${basePath}/documento/${data.id}/`,
      data: data,
      method: 'DELETE'
    })
  }
}
