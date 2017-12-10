const basePath = '/api'
import axios from 'axios'

axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'

const DocumentoActions = {
  getDocumento: { method: 'GET', url: `${basePath}/documento/{/id}` },
  persistDocumento: { method: 'POST', url: `${basePath}/documento/{/id}/create` },
  updateDocumento: { method: 'PUT', url: `${basePath}/documento/{/id}/update` },
  removeDocumento: { method: 'DELETE', url: `${basePath}/documento/{/id}/delete` },
};

export const DocumentoResource = {
  getDocumento: id => axios({
    url: `${basePath}/documento/${id}/`,
    method: 'GET'
  }),
  createDocumento: (data) => axios({
    url: `${basePath}/documento/`,
    data: data,
    method: 'POST'
  }),
  putDocumento: (data) => axios({
    url: `${basePath}/documento/${data.id}/`,
    data: data,
    method: 'PUT'
  }),
  updateDocumento: (data) => axios({
    url: `${basePath}/documento/${data.id}/`,
    data: data,
    method: 'PATCH'
  }),
  uploadFiles: (id, form) => axios({
    url: `${basePath}/documento/${id}/`,
    data: form,
    method: 'PATCH'
  }),
  deleteDocumento: (id) => axios({
    url: `${basePath}/documento/${id}/`,
    method: 'DELETE'
  })
}
