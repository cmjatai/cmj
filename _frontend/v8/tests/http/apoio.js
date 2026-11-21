// Apoio aos testes do cliente HTTP: respostas prontas e leitura das chamadas ao fetch.
import { vi } from 'vitest'

export function respostaJson(corpo, status = 200) {
  return new Response(JSON.stringify(corpo), {
    status,
    headers: { 'Content-Type': 'application/json' }
  })
}

export function respostaHtml(texto, status = 200) {
  return new Response(texto, {
    status,
    headers: { 'Content-Type': 'text/html; charset=utf-8' }
  })
}

export function respostaVazia(status = 204) {
  return new Response(null, { status })
}

// Substitui o fetch global. `responder(url, init)` devolve a Response de cada chamada.
export function simularFetch(responder = () => respostaJson({})) {
  const simulado = vi.fn(async (url, init) => responder(new URL(url), init))
  vi.stubGlobal('fetch', simulado)
  return simulado
}

// A chamada de número `indice` ao fetch, com a URL já interpretada.
export function chamada(simulado, indice = 0) {
  const [url, init] = simulado.mock.calls[indice]
  return { url: new URL(url), init, headers: init.headers }
}

// Chamadas feitas a um caminho, na ordem.
export function chamadasPara(simulado, caminho) {
  return simulado.mock.calls
    .map(([url, init]) => ({ url: new URL(url), init, headers: init.headers }))
    .filter(c => c.url.pathname === caminho)
}

export function definirCookie(nome, valor) {
  document.cookie = `${nome}=${valor}; Path=/`
}

// Deixa as promessas pendentes avançarem.
export async function assentar(voltas = 20) {
  for (let i = 0; i < voltas; i += 1) {
    await Promise.resolve()
  }
  await new Promise(resolver => setTimeout(resolver, 0))
}

// Captura a rejeição de uma promessa sem deixar o teste passar se ela resolver.
export async function erroDe(promessa) {
  try {
    await promessa
  } catch (erro) {
    return erro
  }
  throw new Error('a promessa deveria ter rejeitado')
}
