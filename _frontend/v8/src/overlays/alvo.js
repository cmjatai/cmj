// Gramática dos alvos de data-drawer, data-modal e da query string `painel` (V8-OVL-050 e 081).
//
//   <nome>:<argumento>   entrada do registro de painéis ou de modals
//   frag:<caminho>       fragmento HTML em /v8/_frag/<caminho>/
//   el:#<id>             elemento já presente na página
//
// O texto nunca é usado como URL nem como seletor livre (V8-OVL-100).

const RE_NOME = /^([a-z][a-z0-9-]*)(?::([A-Za-z0-9_-]*))?$/
const RE_CAMINHO = /^[A-Za-z0-9_-]+(?:\/[A-Za-z0-9_-]+)*$/
const RE_ID = /^#([A-Za-z][A-Za-z0-9_-]*)$/

export function interpretarAlvo(texto) {
  if (typeof texto !== 'string') {
    return null
  }
  const valor = texto.trim()
  if (valor.startsWith('frag:')) {
    const caminho = valor.slice(5)
    return RE_CAMINHO.test(caminho) ? { tipo: 'frag', caminho } : null
  }
  if (valor.startsWith('el:')) {
    const achado = RE_ID.exec(valor.slice(3))
    return achado ? { tipo: 'el', id: achado[1] } : null
  }
  const achado = RE_NOME.exec(valor)
  if (!achado || achado[1] === 'frag' || achado[1] === 'el') {
    return null
  }
  return { tipo: 'nome', nome: achado[1], arg: achado[2] || '' }
}

// URL do fragmento: sempre na mesma origem e sob a base de fragmentos.
export function urlDoFragmento(caminho, base = '/v8/_frag/') {
  if (!RE_CAMINHO.test(caminho)) {
    return null
  }
  return `${base}${caminho}/`
}

// Conteúdo e opções de um alvo, ou null quando ele não pode ser aberto.
export function resolverAlvo(texto, registro = {}) {
  const alvo = interpretarAlvo(texto)
  if (!alvo) {
    return null
  }
  if (alvo.tipo === 'frag') {
    return { alvo, conteudo: { frag: alvo.caminho }, opcoes: {} }
  }
  if (alvo.tipo === 'el') {
    return { alvo, conteudo: { el: alvo.id }, opcoes: {} }
  }
  if (!Object.hasOwn(registro, alvo.nome)) {
    return null
  }
  const definicao = registro[alvo.nome]
  return {
    alvo,
    conteudo: {
      componente: definicao.componente,
      props: definicao.props ? definicao.props(alvo.arg) : {}
    },
    opcoes: { ...(definicao.opcoes || {}) }
  }
}
