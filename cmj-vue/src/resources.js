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
  setDocumento: (data, route) => axios({
    url: `${basePath}/documento/${data.id}/${route}/`,
    data: data,
    method: 'POST'
  })
}
