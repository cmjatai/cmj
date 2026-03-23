/**
 * Helpers reutilizáveis para o módulo de Prestação de Contas LOA.
 * Extraídos do PrestacaoContaLoaLayout para uso em componentes filhos.
 */

const TIPO_LABELS = {
  0: 'Emenda Modificativa',
  10: 'Emenda Impositiva Saúde',
  99: 'Emenda Impositiva Áreas Diversas'
}

const TIPO_VARIANTS = {
  0: 'secondary',
  10: 'success',
  99: 'info'
}

const FASE_VARIANTS = {
  20: 'secondary',
  25: 'info',
  30: 'info',
  40: 'danger',
  50: 'warning',
  60: 'warning',
  99: 'success'
}

const FASE_LABELS = {
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

const SITUACAO_VARIANTS = {
  EM_EXECUCAO: 'warning',
  FINALIZADO: 'success',
  SEM_PRESTACAO_CONTAS: 'secondary'
}

const SITUACAO_LABELS = {
  EM_EXECUCAO: 'Em Execução',
  FINALIZADO: 'Finalizado',
  SEM_PRESTACAO_CONTAS: 'Sem Prestação de Contas'
}

export function tipoVariant (tipo) {
  return TIPO_VARIANTS[tipo] || 'light'
}

export function tipoLabel (tipo) {
  return TIPO_LABELS[tipo] || `Tipo ${tipo}`
}

export function faseVariant (fase) {
  return FASE_VARIANTS[fase] || 'light'
}

export function faseLabel (fase) {
  return FASE_LABELS[fase] || `Fase ${fase}`
}

export function situacaoVariant (situacao) {
  return SITUACAO_VARIANTS[situacao] || 'light'
}

export function situacaoLabel (situacao) {
  return SITUACAO_LABELS[situacao] || situacao
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
