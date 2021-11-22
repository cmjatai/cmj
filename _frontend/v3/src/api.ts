import axios from 'axios'

const basePath = `${import.meta.env.V3_API_URL}`

axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'

const call_axios = function (obj:Object) {
  // console.log(obj)
  return axios(obj)
}

export default {
  getModelList: (a: string, m: string, page = 1, query_string = '') => call_axios({
    url: `${basePath}/${a}/${m}/?page=${page}${query_string}`,
    method: 'GET'
  })
}