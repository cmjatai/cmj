import axios from 'axios'

//const basePath = `${import.meta.env.V3_API_URL}`
const V3_API_BACKEND= 'https://www.jatai.go.leg.br'
const V3_API_FRONTEND= 'http://localhost:3000'

axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'

const call_axios = function (obj:Object) {
  // console.log(obj)
  return axios(obj)
}

export default {
  getModelList: (a: string, m: string, page = 1, query_string = '') => call_axios({
    url: `${V3_API_FRONTEND}/api/${a}/${m}/?page=${page}${query_string}`,
    method: 'GET'
  }),
  get: (_url:string) => call_axios({
    url: `${V3_API_BACKEND}${_url}`,
    method: 'GET'
  })
}