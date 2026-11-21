import pinia from '~@/core/pinia'
import { paineis } from '~@/core/paineis'
import { useOverlayStore } from '~@/overlays/OverlayStore'
import { resolverAlvo } from '~@/overlays/alvo'

// Drawers de painel guardados na query string `painel` (V8-OVL-050 a 052).
//
// A URL é a fonte: abrir é empurrar um valor para a query, e fechar é tirá-lo. O store só
// acompanha, depois de cada navegação. Por isso o botão voltar fecha e o link é compartilhável.

let router = null
let registro = paineis
let agendado = false
const opcoesDoGatilho = new Map()
const aFechar = new Set()

function definicao(valor) {
  const resolvido = resolverAlvo(valor, registro)
  return resolvido && resolvido.alvo.tipo !== 'el' ? resolvido : null
}

// Valores de `painel` que podem ser abertos, na ordem da URL. O resto é ignorado (V8-OVL-100).
export function valoresDaQuery(query) {
  const bruto = query?.painel
  const lista = Array.isArray(bruto) ? bruto : (bruto ? [bruto] : [])
  return lista.filter((valor, i) => typeof valor === 'string' && lista.indexOf(valor) === i && definicao(valor))
}

function entradasDaQuery(store) {
  return store.entradas.filter(e => e.source === 'query')
}

// Quantas entradas abertas continuam valendo para a lista desejada.
function mantidas(abertas, desejados) {
  let k = 0
  while (k < abertas.length && k < desejados.length && abertas[k].chave === desejados[k]) {
    k += 1
  }
  return k
}

// Antes de navegar: se a navegação fecharia um overlay com alteração, pergunta (V8-OVL-024).
async function guarda(to) {
  const store = useOverlayStore(pinia)
  const abertas = entradasDaQuery(store)
  const caminhos = to.matched.map(r => r.path)
  const saem = [
    ...abertas.slice(mantidas(abertas, valoresDaQuery(to.query))),
    ...store.entradas.filter(e => e.source === 'rota' && !caminhos.includes(e.chave))
  ]
  if (!saem.length) {
    return true
  }
  const ids = new Set()
  saem.forEach(e => store.comAsDeCima(e.id).forEach(acima => ids.add(acima.id)))
  return store.podeDescartar([...ids])
}

// Depois de navegar: deixa o store igual à URL.
function reconciliar(desejados) {
  const store = useOverlayStore(pinia)
  const abertas = entradasDaQuery(store)
  const k = mantidas(abertas, desejados)
  abertas.slice(k).reverse().forEach(entrada => {
    store.comAsDeCima(entrada.id)
      .filter(acima => acima.id === entrada.id || acima.source === 'local')
      .forEach(acima => store.remover(acima.id))
  })
  desejados.slice(k).forEach(valor => {
    const resolvido = definicao(valor)
    store.openDrawer(resolvido.conteudo, {
      side: 'right',
      size: 'md',
      ...resolvido.opcoes,
      ...(opcoesDoGatilho.get(valor) || {}),
      source: 'query',
      chave: valor,
      fechador: () => agendarFechamento(valor)
    })
    opcoesDoGatilho.delete(valor)
  })
}

// Fechar pela interface: volta no histórico quando foi este app que empurrou a entrada, para
// que o avançar reabra. Em link aberto direto, troca a URL no lugar.
function agendarFechamento(chave) {
  aFechar.add(chave)
  if (!agendado) {
    agendado = true
    queueMicrotask(executarFechamento)
  }
}

function executarFechamento() {
  agendado = false
  const rota = router.currentRoute.value
  const atuais = valoresDaQuery(rota.query)
  const indices = [...aFechar].map(chave => atuais.indexOf(chave)).filter(i => i >= 0)
  aFechar.clear()
  if (!indices.length) {
    return
  }
  const manter = atuais.slice(0, Math.min(...indices))
  const fechados = atuais.length - manter.length
  if ((window.history.state?.v8Paineis || 0) >= fechados) {
    router.go(-fechados)
    return
  }
  const query = { ...rota.query }
  if (manter.length) {
    query.painel = manter
  } else {
    delete query.painel
  }
  router.replace({ path: rota.path, query, hash: rota.hash })
}

// Diz se o valor pode virar um painel: há router e o registro o conhece.
export function podeAbrirPainel(valor) {
  return Boolean(router && definicao(valor))
}

// Abre um painel pondo o valor em ?painel=. Devolve false quando o valor não pode ser aberto.
export function abrirPainel(valor, opcoes = {}) {
  if (!router || !definicao(valor)) {
    return Promise.resolve(false)
  }
  const rota = router.currentRoute.value
  const atuais = valoresDaQuery(rota.query)
  if (atuais.includes(valor)) {
    return Promise.resolve(false)
  }
  opcoesDoGatilho.set(valor, opcoes)
  return router
    .push({
      path: rota.path,
      query: { ...rota.query, painel: [...atuais, valor] },
      hash: rota.hash,
      state: { v8Paineis: (window.history.state?.v8Paineis || 0) + 1 }
    })
    .then(falha => !falha)
}

export function instalarSincroniaDePaineis(novoRouter, opcoes = {}) {
  router = novoRouter
  registro = opcoes.registro || paineis
  opcoesDoGatilho.clear()
  aFechar.clear()
  agendado = false
  router.beforeEach(guarda)
  // Usa a rota em vigor, e não o destino: uma navegação recusada não muda a pilha.
  router.afterEach(() => reconciliar(valoresDaQuery(router.currentRoute.value.query)))
}
