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
    fetch: (m) => {
      if (m.params && !m.query_string) {
        const params = new URLSearchParams(m.params)
        m.query_string = params.toString()
      }
      return axios({
        url: `${basePath}/${m.app}/${m.model}/${m.id ? m.id + '/' : ''}${m.action ? m.action + '/' : ''}${m.query_string ? '?' : ''}${m.query_string ? m.query_string : ''}`,
        method: 'GET'
      })
    },

    patchModelAction: (m) => axios.patch(
      `${basePath}/${m.app}/${m.model}/${m.id}/${m.action}/`,
      m.form || {},
      m.progress || {}
    ),
    patchModel: (m) => axios.patch(
      `${basePath}/${m.app}/${m.model}/${m.id}/`,
      m.form || {},
      m.progress || {}
    ),
    createModel: (m) => axios.post(
      `${basePath}/${m.app}/${m.model}/`,
      m.form || {},
      m.progress || {}
    ),
    deleteModel: (m) => axios.delete(
      `${basePath}/${m.app}/${m.model}/${m.id}/`
    )
  }
}
// app, model, id, action, form, progress = {}
