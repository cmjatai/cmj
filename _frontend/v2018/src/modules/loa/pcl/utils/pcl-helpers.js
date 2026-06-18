/**
 * Helpers reutilizáveis para o módulo de Prestação de Contas LOA.
 * Extraídos do PrestacaoContaLoaLayout para uso em componentes filhos.
 */

const TIPO_EMENDA_LABELS = {
  0: 'Emenda Modificativa',
  10: 'Emenda Impositiva Saúde',
  99: 'Emenda Impositiva Áreas Diversas'
}
const TIPO_EMENDA_VARIANTS = {
  0: 'secondary',
  10: 'success',
  99: 'info'
}
const FASE_EMENDA_VARIANTS = {
  20: 'secondary',
  25: 'info',
  30: 'info',
  40: 'danger',
  50: 'warning',
  60: 'warning',
  99: 'success'
}
const FASE_EMENDA_LABELS = {
  10: 'Proposta',
  12: 'Proposta Liberada',
  15: 'Edição Contábil',
  17: 'Liberado Contab.',
  20: 'Em Tramitação',
  25: 'Aprov. Legislativa',
  30: 'Aprovada',
  40: 'Impedimento',
  50: 'Emenda Redefinida/Sanada',
  60: 'Em Execução',
  99: 'Finalizada'
}

const SITUACAO_EMENDA_VARIANTS = {
  EM_EXECUCAO: 'warning',
  FINALIZADO: 'success'
}

const SITUACAO_EMENDA_LABELS = {
  EM_EXECUCAO: 'Em Execução',
  FINALIZADO: 'Finalizada'
}

const TIPO_AJUSTE_LABELS = {
  10: 'Ajuste Saúde',
  99: 'Ajuste Áreas Diversas'
}
const TIPO_AJUSTE_VARIANTS = {
  10: 'success',
  99: 'info'
}
const FASE_AJUSTE_VARIANTS = {
  10: 'secondary',
  40: 'danger',
  60: 'warning',
  90: 'success'
}
const FASE_AJUSTE_LABELS = {
  10: 'Registrado',
  40: 'Impedimento',
  60: 'Em Execução',
  90: 'Finalizado'
}
const SITUACAO_AJUSTE_VARIANTS = {
  REGISTRADO: 'secondary',
  IMPEDIMENTO: 'danger',
  EM_EXECUCAO: 'warning',
  FINALIZADO: 'success'
}

const SITUACAO_AJUSTE_LABELS = {
  REGISTRADO: 'Registrado',
  IMPEDIMENTO: 'Impedimento',
  EM_EXECUCAO: 'Em Execução',
  FINALIZADO: 'Finalizado'
}

const PRESTACAO_CONTA_VARIANTS = {
  EM_EXECUCAO: 'warning',
  FINALIZADO: 'success'
}

const PRESTACAO_CONTA_LABELS = {
  EM_EXECUCAO: 'Em Análise/Execução',
  FINALIZADO: 'Finalizada'
}

export function prestacaoContaVariant (situacao) {
  return PRESTACAO_CONTA_VARIANTS[situacao] || 'light'
}

export function prestacaoContaLabel (situacao) {
  return PRESTACAO_CONTA_LABELS[situacao] || situacao
}

export function tipoVariant (tipo, isAjuste = false) {
  if (isAjuste) {
    return TIPO_AJUSTE_VARIANTS[tipo] || 'light'
  }
  return TIPO_EMENDA_VARIANTS[tipo] || 'light'
}

export function tipoLabel (tipo, isAjuste = false) {
  if (isAjuste) {
    return TIPO_AJUSTE_LABELS[tipo] || `Tipo ${tipo}`
  }
  return TIPO_EMENDA_LABELS[tipo] || `Tipo ${tipo}`
}

export function faseVariant (fase, isAjuste = false) {
  if (isAjuste) {
    return FASE_AJUSTE_VARIANTS[fase] || 'light'
  }
  return FASE_EMENDA_VARIANTS[fase] || 'light'
}

export function faseLabel (fase, isAjuste = false) {
  if (isAjuste) {
    return FASE_AJUSTE_LABELS[fase] || `Fase ${fase}`
  }
  return FASE_EMENDA_LABELS[fase] || `Fase ${fase}`
}

export function situacaoVariant (situacao, isAjuste = false) {
  if (isAjuste) {
    return SITUACAO_AJUSTE_VARIANTS[situacao] || 'light'
  }
  return SITUACAO_EMENDA_VARIANTS[situacao] || 'light'
}

export function situacaoLabel (situacao, isAjuste = false) {
  if (isAjuste) {
    return SITUACAO_AJUSTE_LABELS[situacao] || situacao
  }
  return SITUACAO_EMENDA_LABELS[situacao] || situacao
}

/**
 * Retorna o variant do badge para um item (emenda ou ajuste).
 */
export function itemBadgeVariant (item) {
  if (item.__label__ === 'loa_emendaloa') {
    return item.tipo !== 0 ? 'primary' : 'secondary'
  }
  return 'warning'
}

/**
 * Retorna o texto do badge para um item (emenda ou ajuste).
 */
export function itemBadgeLabel (item) {
  if (item.__label__ === 'loa_emendaloa') {
    return item.tipo !== 0 ? 'Emenda Impositiva' : 'Emenda Modificativa'
  }
  return 'Ajuste'
}

/**
 * Retorna o texto do badge para o registro selecionado (header do detalhe).
 */
export function registroBadgeLabel (registro) {
  if (registro.__label__ === 'loa_emendaloa') {
    return registro.tipo !== 0 ? 'Emenda Impositiva' : 'Emenda Modificativa'
  }
  return 'Registro de Ajuste'
}

/**
 * Verifica se o registro é uma emenda LOA.
 */
export function isEmenda (registro) {
  return registro && registro.__label__ === 'loa_emendaloa'
}

/**
 * Formata data ISO (yyyy-mm-dd) para formato brasileiro (dd/mm/yyyy).
 */
export function formatDateBR (dateStr) {
  if (!dateStr) return '—'
  return dateStr.split('-').reverse().join('/')
}
