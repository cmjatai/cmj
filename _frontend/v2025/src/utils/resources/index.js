import axios from 'axios'
const basePath = '/api'

axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'

export default {
  Utils: {
    fetch: (m) => axios({
      url: `${basePath}/${m.app}/${m.model}/${m.id ? m.id + '/' : ''}${m.action ? m.action + '/' : ''}${m.query_string ? '?' : ''}${m.query_string ? m.query_string : ''}`,
      method: 'GET'
    }),
    patchModelAction: (m) => axios.patch(
      `${basePath}/${m.app}/${m.model}/${m.id}/${m.action}/`,
      m.form || {},
      m.progress || {}
    ),
    patchModel: (m) => axios.patch(
      `${basePath}/${m.app}/${m.model}/${m.id}/`,
      m.form || {},
      m.progress || {}
    )
  }
}
// app, model, id, action, form, progress = {}
