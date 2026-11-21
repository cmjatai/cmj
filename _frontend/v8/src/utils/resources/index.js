import pinia from '~@/core/pinia'
import http from '~@/http/client'
import { useGlobalStore } from '~@/stores/GlobalStore'

// Resources.Utils sobre o cliente HTTP único (V8-HTTP-030). As assinaturas são as que o v8 herdou
// do v6 e cada função resolve com { data }, como o axios fazia. Erro rejeita com HttpError.
// Os cabeçalhos no-cache que o v6 mandava em todo GET deram lugar ao `cache: 'no-store'` que o
// cliente passa ao fetch.
// Não há `login`: o v8 não trafega credencial, a autenticação é só na tela /login/ (V8-HTTP-043).

function urls() {
  return useGlobalStore(pinia).urls
}

// Raiz da API sem barra final, como o '/api' fixo que havia aqui.
function basePath() {
  return String(urls().api).replace(/\/+$/, '')
}

function caminho(m, comId = true) {
  const id = comId && m.id ? m.id + '/' : ''
  const action = m.action ? m.action + '/' : ''
  return `${basePath()}/${m.app}/${m.model}/${id}${action}`
}

function comoData(promessa) {
  return promessa.then(data => ({ data }))
}

// TODO: refatorar para aproveitar cache e LastModified
export default {
  Utils: {
    logout: () => comoData(http.delete(urls().sessao)),
    hasPermission: (permission) => {
      return http.request('OPTIONS', urls().sessao, { params: { perm: permission } })
        .then(data => {
          return data?.status === 'ok'
        })
        .catch(() => {
          return false
        })
    },
    getVersion: () => comoData(http.get(urls().versao)),
    fetch: (m, method = 'GET') => {
      if (m.params && !m.query_string) {
        const params = new URLSearchParams(m.params)
        m.query_string = params.toString()
      }
      const url = `${caminho(m)}${m.query_string ? '?' : ''}${m.query_string ? m.query_string : ''}`
      return comoData(http.request(method, url))
    },
    // `m.progress` era a configuração de upload do axios e não tem mais efeito.
    patchModel: (m) => comoData(http.patch(caminho(m), m.form || {})),
    putModel: (m) => comoData(http.put(caminho(m), m.form || {})),
    postModel: (m) => comoData(http.post(caminho(m, false), m.form || {})),
    deleteModel: (m) => comoData(http.delete(`${basePath()}/${m.app}/${m.model}/${m.id}/`))
  }
}
// app, model, id, action, form, progress = {}
