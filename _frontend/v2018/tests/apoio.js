// Apoio comum: axios falso, para que nenhum teste faça requisição de verdade.
import { vi } from 'vitest'

// Uso: vi.mock('axios', async () => (await import('<caminho>/apoio')).axiosFalso())
// As chamadas ficam em `axios.mock.calls` (forma `axios({ url, method })`) e em
// `axios.get/post/patch/delete.mock.calls`.
export function axiosFalso (resposta = { data: {} }) {
  const axios = vi.fn(() => Promise.resolve(resposta))
  ;['get', 'post', 'patch', 'put', 'delete'].forEach(metodo => {
    axios[metodo] = vi.fn(() => Promise.resolve(resposta))
  })
  axios.defaults = { headers: { get: {}, common: {} } }
  return { default: axios }
}

export const esperar = (ms = 0) => new Promise(resolve => setTimeout(resolve, ms))
