// Amostras do design system (docs/specs/v8/ds.md): textos fixos e a validação local dos
// formulários de exemplo. Nada aqui chama o servidor (V8-DS-044).
import { HttpError } from '~@/http/client'

export const NIVEIS_DE_TOAST = [
  { nivel: 'success', rotulo: 'Sucesso', texto: 'Registro salvo.' },
  { nivel: 'info', rotulo: 'Informação', texto: 'Há uma atualização disponível.' },
  { nivel: 'warning', rotulo: 'Aviso', texto: 'O prazo termina amanhã.' },
  { nivel: 'error', rotulo: 'Erro', texto: 'Não foi possível salvar.' }
]

export const BAIRROS = ['Centro', 'Vila Nova', 'Jardim Sul', 'Setor Norte']

function texto(valor) {
  return String(valor ?? '').trim()
}

// Erros por campo, no formato dos erros do Django; objeto vazio quer dizer válido.
export function validarIdentificacao(dados) {
  const erros = {}
  if (texto(dados.nome).length < 3) {
    erros.nome = ['Informe ao menos três letras.']
  }
  if (!texto(dados.email).includes('@')) {
    erros.email = ['Informe um e-mail válido.']
  }
  return erros
}

export function validarBairro(dados) {
  return BAIRROS.includes(dados.bairro) ? {} : { bairro: ['Escolha um bairro.'] }
}

// Simula a resposta de um endpoint: erro de validação como HttpError, sucesso com os dados.
export async function enviarAmostra(dados) {
  const erros = validarIdentificacao(dados)
  if (Object.keys(erros).length) {
    throw new HttpError({ status: 400, codigo: 'validacao', campos: erros })
  }
  return { ...dados }
}

export const passosDoAssistente = [
  {
    titulo: 'Identificação',
    componente: () => import('~@/modules/ds/modais/PassoIdentificacao.vue'),
    validar: validarIdentificacao
  },
  {
    titulo: 'Bairro',
    componente: () => import('~@/modules/ds/modais/PassoBairro.vue'),
    validar: validarBairro
  }
]
