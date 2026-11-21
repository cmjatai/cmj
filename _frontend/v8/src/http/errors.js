// Formato único de erro do cliente HTTP (docs/specs/v8/http.md, V8-HTTP-010 a 012).

export const MENSAGENS_PADRAO = {
  validacao: 'Verifique os dados informados.',
  nao_autenticado: 'Sua sessão expirou. Entre novamente para continuar.',
  sem_permissao: 'Você não tem permissão para executar esta ação.',
  nao_encontrado: 'O que você procura não foi encontrado.',
  conflito: 'A operação entrou em conflito com o estado atual dos dados.',
  servidor: 'O servidor encontrou um erro. Tente novamente em instantes.',
  rede: 'Não foi possível comunicar com o servidor.',
  cancelada: 'Requisição cancelada.'
}

// Chaves que não são nome de campo: reúnem os erros do registro como um todo.
const CHAVES_GERAIS = ['non_field_errors', '__all__']

export class HttpError extends Error {
  constructor({ status = 0, codigo = 'rede', mensagem = '', campos = {}, gerais = [], resposta = null } = {}) {
    const texto = mensagem || MENSAGENS_PADRAO[codigo] || MENSAGENS_PADRAO.rede
    super(texto)
    this.name = 'HttpError'
    this.status = status
    this.codigo = codigo
    this.mensagem = texto
    this.campos = campos
    this.gerais = gerais
    this.resposta = resposta
  }
}

export function codigoDoStatus(status) {
  if (status === 400 || status === 422) {
    return 'validacao'
  }
  if (status === 401) {
    return 'nao_autenticado'
  }
  if (status === 403) {
    return 'sem_permissao'
  }
  if (status === 404) {
    return 'nao_encontrado'
  }
  if (status === 409) {
    return 'conflito'
  }
  if (status >= 500) {
    return 'servidor'
  }
  return 'rede'
}

function ehObjeto(valor) {
  return valor !== null && typeof valor === 'object' && !Array.isArray(valor)
}

function ehMensagem(valor) {
  return typeof valor === 'string'
}

function acrescentar(campos, chave, mensagens) {
  if (mensagens.length) {
    campos[chave] = (campos[chave] || []).concat(mensagens)
  }
}

// Percorre o erro de um campo. Texto vale como lista de um item, objeto aninhado vira chave com
// ponto (endereco.cep) e lista de objetos usa o índice (itens.0.nome).
function achatar(valor, chave, campos) {
  if (ehMensagem(valor)) {
    acrescentar(campos, chave, [valor])
  } else if (Array.isArray(valor)) {
    valor.forEach((item, indice) => {
      if (ehMensagem(item)) {
        acrescentar(campos, chave, [item])
      } else {
        achatar(item, `${chave}.${indice}`, campos)
      }
    })
  } else if (ehObjeto(valor)) {
    Object.keys(valor).forEach(nome => {
      // Erro geral de um objeto aninhado pertence ao próprio objeto.
      achatar(valor[nome], CHAVES_GERAIS.includes(nome) ? chave : `${chave}.${nome}`, campos)
    })
  }
}

function listaDeMensagens(valor) {
  const campos = {}
  achatar(valor, '_', campos)
  return Object.values(campos).flat()
}

function camposDe(objeto, ignoradas = []) {
  const campos = {}
  Object.keys(objeto).forEach(nome => {
    if (!ignoradas.includes(nome) && !CHAVES_GERAIS.includes(nome)) {
      achatar(objeto[nome], nome, campos)
    }
  })
  return campos
}

function geraisDe(...objetos) {
  return objetos.flatMap(objeto => CHAVES_GERAIS.flatMap(chave => listaDeMensagens(objeto[chave])))
}

// Reduz o corpo de erro do DRF e o corpo de erro do v8 a { detail, campos, gerais } (V8-HTTP-012).
//   DRF: { campo: [..], non_field_errors: [..], detail: '..' }
//   v8:  { detail: '..', errors: { campo: [..] }, non_field_errors: [..] }
// Corpo que não é JSON (uma página de erro em HTML, por exemplo) não fornece mensagem.
export function normalizarCorpo(corpo) {
  if (Array.isArray(corpo)) {
    // O DRF responde uma lista quando a validação falha fora de um campo.
    const campos = {}
    const gerais = []
    corpo.forEach((item, indice) => {
      if (ehMensagem(item)) {
        gerais.push(item)
      } else {
        achatar(item, String(indice), campos)
      }
    })
    return { detail: '', campos, gerais }
  }
  if (!ehObjeto(corpo)) {
    return { detail: '', campos: {}, gerais: [] }
  }
  const detail = typeof corpo.detail === 'string' ? corpo.detail : ''
  if (ehObjeto(corpo.errors)) {
    return {
      detail,
      campos: camposDe(corpo.errors),
      gerais: geraisDe(corpo, corpo.errors)
    }
  }
  return {
    detail,
    campos: camposDe(corpo, detail ? ['detail'] : []),
    gerais: geraisDe(corpo)
  }
}

// Monta o HttpError de uma resposta com status de erro. `codigo` só é informado quando o status
// sozinho não decide, como na sessão expirada.
export function erroDaResposta(status, corpo = null, codigo = null) {
  const { detail, campos, gerais } = normalizarCorpo(corpo)
  return new HttpError({
    status,
    codigo: codigo || codigoDoStatus(status),
    mensagem: detail,
    campos,
    gerais,
    resposta: corpo
  })
}

export function erroDeRede(mensagem = '') {
  return new HttpError({ codigo: 'rede', mensagem })
}

export function erroCancelada() {
  return new HttpError({ codigo: 'cancelada' })
}

export function erroNaoAutenticado(status = 401, corpo = null) {
  return erroDaResposta(status, corpo, 'nao_autenticado')
}
