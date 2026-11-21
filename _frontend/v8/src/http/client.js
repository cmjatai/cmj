// Cliente HTTP único do v8 (docs/specs/v8/http.md).
//
// É o único arquivo de src/ que chama fetch (V8-HTTP-001). Cuida do CSRF, entrega os erros
// sempre como HttpError e passa a sessão expirada para ./sessao.js. Não mostra aviso nenhum:
// quem chama decide entre toast, erro no formulário ou nada (V8-HTTP-014).
//
// client.js e sessao.js importam um ao outro. Funciona porque cada um só usa o outro dentro de
// funções, nunca durante a carga do módulo.
import { HttpError, erroCancelada, erroDaResposta, erroDeRede } from './errors'
import { tratarFalhaDeSessao } from './sessao'

const METODOS_COM_CSRF = ['POST', 'PUT', 'PATCH', 'DELETE']

// Erros que já foram para o console: o de uma requisição refeita passa duas vezes por executar().
const registrados = new WeakSet()

function lerCookie(nome) {
  const prefixo = `${nome}=`
  const achado = document.cookie
    .split(';')
    .map(parte => parte.trim())
    .find(parte => parte.startsWith(prefixo))
  return achado ? decodeURIComponent(achado.slice(prefixo.length)) : ''
}

// Resolve a URL como o navegador faria e recusa a que sai da origem da página (V8-HTTP-040).
// O fetch recebe o endereço já resolvido, para não haver segunda interpretação.
function resolverUrl(url, params) {
  let destino
  try {
    destino = new URL(String(url), document.baseURI)
  } catch {
    throw erroDeRede('Endereço inválido.')
  }
  if (destino.origin !== window.location.origin) {
    throw erroDeRede('O endereço está fora deste site e a requisição não foi enviada.')
  }
  Object.keys(params || {}).forEach(chave => {
    const valores = Array.isArray(params[chave]) ? params[chave] : [params[chave]]
    valores.forEach(valor => {
      if (valor !== null && valor !== undefined) {
        destino.searchParams.append(chave, valor)
      }
    })
  })
  return destino
}

// Objeto literal e lista vão como JSON. FormData, Blob, URLSearchParams e texto vão como estão.
function vaiComoJson(valor) {
  if (valor === null || typeof valor !== 'object') {
    return false
  }
  const prototipo = Object.getPrototypeOf(valor)
  return prototipo === Object.prototype || prototipo === null || Array.isArray(valor)
}

// O corpo é preparado uma única vez por requisição: a refeita depois da reautenticação envia
// exatamente o que a original enviou, mesmo que o objeto de quem chamou tenha mudado.
function prepararCorpo(corpo) {
  if (corpo === undefined || corpo === null) {
    return { body: undefined, json: false }
  }
  if (vaiComoJson(corpo)) {
    return { body: JSON.stringify(corpo), json: true }
  }
  return { body: corpo, json: false }
}

function montarPedido(metodo, opcoes, corpo) {
  const headers = new Headers(opcoes.headers || {})
  headers.set('X-Requested-With', 'XMLHttpRequest')
  headers.set('Accept', opcoes.accept === 'html' ? 'text/html' : 'application/json')
  if (METODOS_COM_CSRF.includes(metodo)) {
    // Lido a cada requisição: o Django troca o token quando o usuário entra (V8-HTTP-003).
    const token = lerCookie('csrftoken')
    if (token) {
      headers.set('X-CSRFToken', token)
    } else {
      headers.delete('X-CSRFToken')
    }
  }
  const pedido = {
    method: metodo,
    headers,
    // Cookies só para a mesma origem, e o navegador barra redirecionamento para fora dela.
    credentials: 'same-origin',
    mode: 'same-origin'
  }
  if (corpo.body !== undefined) {
    if (corpo.json) {
      headers.set('Content-Type', 'application/json')
    } else if (corpo.body instanceof FormData) {
      // No FormData é o navegador quem define o Content-Type, com o delimitador das partes.
      headers.delete('Content-Type')
    }
    pedido.body = corpo.body
  }
  if (opcoes.signal) {
    pedido.signal = opcoes.signal
  }
  if (opcoes.cache) {
    pedido.cache = opcoes.cache
  } else if (metodo === 'GET') {
    // GET nunca sai do cache do navegador. Substitui os cabeçalhos no-cache que o v6 mandava.
    pedido.cache = 'no-store'
  }
  return pedido
}

function foiCancelada(erro, signal) {
  return Boolean(signal?.aborted) || erro?.name === 'AbortError'
}

async function lerCorpo(resposta) {
  if (resposta.status === 204 || resposta.status === 205) {
    return null
  }
  const texto = await resposta.text()
  if (!texto) {
    return null
  }
  const tipo = resposta.headers.get('Content-Type') || ''
  if (!tipo.includes('json')) {
    return texto
  }
  try {
    return JSON.parse(texto)
  } catch {
    if (resposta.ok) {
      throw erroDeRede('O servidor enviou uma resposta que não pôde ser lida.')
    }
    return texto
  }
}

// O registro no console leva só método, caminho e código: nunca o corpo da requisição, nem a
// query string, nem o corpo da resposta (V8-HTTP-045).
function registrar(metodo, destino, erro) {
  if (!(erro instanceof HttpError) || registrados.has(erro)) {
    return
  }
  registrados.add(erro)
  if (erro.codigo === 'servidor' || erro.codigo === 'rede') {
    console.warn(`[http] ${metodo} ${destino ? destino.pathname : '(endereço recusado)'}: ${erro.codigo} (${erro.status})`)
  }
}

// `enviado` é o corpo já preparado, presente só quando a requisição está sendo refeita.
async function executar(metodo, url, opcoes, enviado = null) {
  let destino = null
  try {
    destino = resolverUrl(url, opcoes.params)
    if (opcoes.signal?.aborted) {
      throw erroCancelada()
    }
    let resposta
    let corpo
    let preparado = enviado
    try {
      preparado = preparado || prepararCorpo(opcoes.corpo)
      resposta = await fetch(destino.href, montarPedido(metodo, opcoes, preparado))
      corpo = await lerCorpo(resposta)
    } catch (erro) {
      if (erro instanceof HttpError) {
        throw erro
      }
      throw foiCancelada(erro, opcoes.signal) ? erroCancelada() : erroDeRede()
    }
    if (resposta.ok) {
      return corpo
    }
    if (!opcoes.semSessao && (resposta.status === 401 || resposta.status === 403)) {
      // Sessão expirada: a requisição pode ficar pendente e ser refeita uma única vez.
      return await tratarFalhaDeSessao({
        status: resposta.status,
        corpo,
        refeita: Boolean(enviado),
        signal: opcoes.signal,
        refazer: () => executar(metodo, url, opcoes, preparado)
      })
    }
    throw erroDaResposta(resposta.status, corpo)
  } catch (erro) {
    registrar(metodo, destino, erro)
    throw erro
  }
}

function request(metodo, url, opcoes = {}) {
  return executar(String(metodo).toUpperCase(), url, opcoes || {})
}

const http = {
  request,
  get: (url, opcoes) => request('GET', url, opcoes),
  delete: (url, opcoes) => request('DELETE', url, opcoes),
  post: (url, corpo, opcoes) => request('POST', url, { ...opcoes, corpo }),
  put: (url, corpo, opcoes) => request('PUT', url, { ...opcoes, corpo }),
  patch: (url, corpo, opcoes) => request('PATCH', url, { ...opcoes, corpo })
}

export { HttpError }
export default http
