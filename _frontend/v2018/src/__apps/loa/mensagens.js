import _ from 'lodash'

// Mensagem do servidor a partir de um erro do axios (LOA-EMD-084 e LOA-AGR-064)
export function mensagemDoErro (error) {
  const response = error && error.response
  if (!response) {
    return 'Não foi possível comunicar com o servidor. Verifique a conexão e tente novamente.'
  }

  const data = response.data
  const generica = `O servidor respondeu com erro ${response.status}.`

  const textos = (valor) => {
    if (_.isString(valor)) return [valor]
    if (_.isArray(valor)) return _.flatMap(valor, textos)
    if (_.isPlainObject(valor)) {
      return _.flatMap(Object.entries(valor), ([chave, v]) => {
        if (chave === 'detail' || chave === 'non_field_errors') return textos(v)
        return textos(v).map((t) => `${chave}: ${t}`)
      })
    }
    return []
  }

  // Página HTML de erro (500, 502...) não é mensagem para o usuário
  if (_.isString(data) && /^\s*</.test(data)) return generica

  const lista = textos(data).filter((t) => t.trim() !== '')
  return lista.length > 0 ? lista.join('\n') : generica
}
