// Passos do wizard "Novo cliente" (V8-DEMO-023), no formato que o ModalWizard espera:
// { titulo, componente, validar }. Cada `validar(dados)` devolve os erros por campo, e objeto
// vazio quer dizer passo válido. A validação que vale é a do servidor, feita ao concluir: estas
// só evitam avançar com o passo incompleto.

export function dadosIniciais() {
  return { nome: '', email: '', cidade: '', situacao: 'ativo', motivo: '' }
}

function texto(valor) {
  return String(valor ?? '').trim()
}

export function validarIdentificacao(dados) {
  const erros = {}
  const letras = texto(dados.nome).match(/\p{L}/gu) || []
  if (letras.length < 3) {
    erros.nome = ['O nome precisa ter ao menos três letras.']
  }
  if (!texto(dados.email).includes('@')) {
    erros.email = ['Informe um e-mail válido.']
  }
  return erros
}

export function validarLocal(dados) {
  const erros = {}
  if (!texto(dados.cidade)) {
    erros.cidade = ['Informe a cidade.']
  }
  if (dados.situacao === 'inativo' && !texto(dados.motivo)) {
    erros.motivo = ['Cliente inativo precisa de um motivo preenchido.']
  }
  return erros
}

export const passosNovoCliente = [
  {
    titulo: 'Identificação',
    componente: () => import('~@/modules/demo/wizard/PassoIdentificacao.vue'),
    validar: validarIdentificacao
  },
  {
    titulo: 'Local e situação',
    componente: () => import('~@/modules/demo/wizard/PassoLocal.vue'),
    validar: validarLocal
  },
  {
    titulo: 'Revisão',
    componente: () => import('~@/modules/demo/wizard/PassoRevisao.vue'),
    validar: () => ({})
  }
]
