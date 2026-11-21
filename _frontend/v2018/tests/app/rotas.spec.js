import { describe, expect, it, vi } from 'vitest'

import { routes } from '@/routers'

vi.mock('axios', async () => (await import('../apoio')).axiosFalso())

function planas (rotas, base = '') {
  return rotas.flatMap(rota => {
    const caminho = rota.path.startsWith('/') ? rota.path : `${base}${rota.path}`
    return [{ ...rota, caminho }, ...planas(rota.children || [], caminho)]
  })
}

describe('rotas da entrada app', () => {
  const todas = planas(routes)

  it('V2018-EST-032: todas as rotas ficam sob /loa/', () => {
    expect(todas.every(rota => rota.caminho.startsWith('/loa/'))).toBe(true)
  })

  it('V2018-EST-032: os nomes de rota são únicos', () => {
    const nomes = todas.map(rota => rota.name).filter(Boolean)
    expect(new Set(nomes).size).toBe(nomes.length)
  })

  it.each(todas.map(rota => [rota.caminho, rota]))(
    'V2018-EST-032: o componente de %s é carregado sob demanda e existe',
    async (caminho, rota) => {
      expect(rota.component).toBeTypeOf('function')
      const modulo = await rota.component()
      expect(modulo.default).toBeTypeOf('object')
    })
})
