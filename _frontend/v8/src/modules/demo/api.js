// API da demonstração (docs/specs/v8/demo.md). O servidor valida e responde como se tivesse
// gravado, mas nada é gravado (V8-DEMO-002). Os erros chegam como HttpError, do cliente HTTP.
import http from '~@/http/client'

const CLIENTES = '/v8/demo/api/clientes/'
const NEGADO = '/v8/demo/api/negado/'

function urlDoCliente(id) {
  return `${CLIENTES}${encodeURIComponent(id)}/`
}

// filtros: { q, situacao, cidade, pagina, tamanho }. Filtro vazio não vai para a URL.
// Resolve com { total, pagina, paginas, tamanho, itens }.
export function listar(filtros = {}) {
  const params = _.omitBy(filtros, valor => valor === '' || valor === null || valor === undefined)
  return http.get(CLIENTES, { params })
}

// Resolve com o cliente e seus pedidos. Id inexistente rejeita com codigo 'nao_encontrado'.
export function obter(id) {
  return http.get(urlDoCliente(id))
}

// dados: { nome, email, cidade, situacao, motivo }. Entrada inválida rejeita com codigo
// 'validacao', e o erro traz `campos` e `gerais`.
export function criar(dados) {
  return http.post(CLIENTES, dados)
}

export function salvar(id, dados) {
  return http.put(urlDoCliente(id), dados)
}

// Responde sempre 403: existe para mostrar o tratamento de 'sem_permissao' (V8-DEMO-025).
export function negado() {
  return http.get(NEGADO)
}
