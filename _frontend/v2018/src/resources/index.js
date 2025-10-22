import axios from 'axios'
const basePath = '/api'

axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'

export default {
  Utils: {
    login: (username, password) => axios.post(
      `${basePath}/auth/session`, {
        username,
        password
      },
      {
        withCredentials: true
      }
    ),
    logout: () => axios.delete(
      `${basePath}/auth/session`
    ),
    hasPermission: (permission) => {
      return axios({
        url: `${basePath}/auth/session/?perm=${permission}`,
        method: 'OPTIONS',
        withCredentials: true
      })
        .then(response => {
          return response.data.status === 'ok'
        })
        .catch(() => {
          return false
        })
    },
    getVersion: () => axios({
      url: `${basePath}/version`,
      method: 'GET'
    }),
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
    getModelAction: (app, model, id, action, query_string = '') => axios({
      url: `${basePath}/${app}/${model}/${id}/${action}/?${query_string}`,
      method: 'GET'
    }),
    getModelListAction: (app, model, action, page = 1) => axios({
      url: `${basePath}/${app}/${model}/${action}/?page=${page}`,
      method: 'GET'
    }),
    getByMetadata: (m, query_string = '') => axios({
      url: `${basePath}/${m.app}/${m.model}/${m.id}${m.id !== '' ? '/' : ''}${m.action}${m.action !== '' ? '/' : ''}${query_string !== '' ? '?' : ''}${query_string}`,
      method: 'GET'
    }),
    postModelAction: (app, model, id, action, form, progress = {}) => axios.post(
      `${basePath}/${app}/${model}/${id}/${action}/`,
      form,
      progress
    ),
    patchModelAction: (app, model, id, action, form, progress = {}) => axios.patch(
      `${basePath}/${app}/${model}/${id}/${action}/`,
      form,
      progress
    ),
    deleteModel: (app, model, id) => axios.delete(
      `${basePath}/${app}/${model}/${id}/`
    ),
    patchModel: (app, model, id, form) => axios.patch(
      `${basePath}/${app}/${model}/${id}/`,
      form
    ),
    postModel: (app, model, form) => axios.post(
      `${basePath}/${app}/${model}/`,
      form
    ),
    fetch: (m) => axios({
      url: `${basePath}/${m.app}/${m.model}/${m.id ? m.id + '/' : ''}${m.action ? m.action + '/' : ''}${m.query_string ? '?' : ''}${m.query_string ? m.query_string : ''}`,
      method: 'GET'
    })
  }
}
