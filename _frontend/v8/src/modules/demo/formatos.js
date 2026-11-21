// Apresentação dos dados da demonstração. A API entrega as datas em ISO (aaaa-mm-dd) e os
// valores como texto decimal ('19.90').

export const SITUACOES = [
  { valor: 'ativo', rotulo: 'Ativo' },
  { valor: 'inativo', rotulo: 'Inativo' }
]

const moeda = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })

export function rotuloDaSituacao(situacao) {
  return SITUACOES.find(item => item.valor === situacao)?.rotulo || ''
}

// A data é lida do próprio texto, sem passar por Date, para não mudar de dia com o fuso.
export function formatarData(iso) {
  const partes = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(iso ?? ''))
  return partes ? `${partes[3]}/${partes[2]}/${partes[1]}` : ''
}

export function formatarValor(valor) {
  const numero = Number(valor)
  return valor === '' || valor === null || !Number.isFinite(numero) ? '' : moeda.format(numero)
}
