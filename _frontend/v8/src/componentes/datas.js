// Conversão entre o texto ISO do v-model dos componentes de data e os objetos de data do Reka UI
// (docs/specs/v8/componentes.md, V8-CMP-030 e 031). É o único lugar que conhece os dois formatos.
//
//   dia: AAAA-MM-DD   hora: HH:MM   mês: AAAA-MM   ano: AAAA   período: { inicio, fim }
//
// Texto que não é uma data válida vale como vazio: o objeto sai `undefined` e o texto, ''.
import { CalendarDate, parseDate, parseTime } from '@internationalized/date'

export const IDIOMA = 'pt-BR'

// Nome de cada parte de uma data ou hora digitada por partes, para o leitor de tela. O Reka UI os
// traz em inglês (V8-CMP-008).
export const NOMES_DAS_PARTES = {
  day: 'dia',
  month: 'mês',
  year: 'ano',
  hour: 'hora',
  minute: 'minuto',
  second: 'segundo',
  dayPeriod: 'período do dia'
}

const DOIS = n => String(n).padStart(2, '0')
const QUATRO = n => String(n).padStart(4, '0')

function tentar(fabrica) {
  try {
    return fabrica()
  } catch {
    return undefined
  }
}

export const dia = {
  paraObjeto: texto => (/^\d{4}-\d{2}-\d{2}$/.test(texto ?? '') ? tentar(() => parseDate(texto)) : undefined),
  paraTexto: valor => (valor ? `${QUATRO(valor.year)}-${DOIS(valor.month)}-${DOIS(valor.day)}` : '')
}

export const hora = {
  paraObjeto: texto => (/^\d{2}:\d{2}$/.test(texto ?? '') ? tentar(() => parseTime(texto)) : undefined),
  paraTexto: valor => (valor ? `${DOIS(valor.hour)}:${DOIS(valor.minute)}` : '')
}

export const mes = {
  paraObjeto: texto => {
    const partes = /^(\d{4})-(\d{2})$/.exec(texto ?? '')
    const numero = partes ? Number(partes[2]) : 0
    return numero >= 1 && numero <= 12 ? new CalendarDate(Number(partes[1]), numero, 1) : undefined
  },
  paraTexto: valor => (valor ? `${QUATRO(valor.year)}-${DOIS(valor.month)}` : '')
}

export const ano = {
  paraObjeto: texto => (/^\d{4}$/.test(texto ?? '') ? new CalendarDate(Number(texto), 1, 1) : undefined),
  paraTexto: valor => (valor ? QUATRO(valor.year) : '')
}

// Período: `{ inicio, fim }` em texto para `{ start, end }` em objetos, e de volta.
export function periodoParaObjeto(periodo, formato) {
  return {
    start: formato.paraObjeto(periodo?.inicio),
    end: formato.paraObjeto(periodo?.fim)
  }
}

export function periodoParaTexto(intervalo, formato) {
  return {
    inicio: formato.paraTexto(intervalo?.start),
    fim: formato.paraTexto(intervalo?.end)
  }
}

