import axios from 'axios'
const basePath = '/api'

axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'

export const DocumentoResource = {
  getDocumentoChoiceList: (tipo, page) => axios({
    url: `${basePath}/documento/?page=${page}&tipo=${tipo}`,
    method: 'GET'
  }),
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
  }),
  deleteReferencia: (data) => axios({
    url: `${basePath}/documento/${data.id}/`,
    data: data,
    method: 'DELETE'
  })
}
