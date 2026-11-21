import { beforeEach, describe, expect, it, vi } from 'vitest'
import axios from 'axios'

import Resources from '@/resources'

vi.mock('axios', async () => (await import('../apoio')).axiosFalso())

const utils = Resources.Utils

describe('Resources.Utils', () => {
  beforeEach(() => {
    axios.mockClear()
  })

  it('V2018-EST-036: configura o CSRF do Django e GET sem cache', () => {
    expect(axios.defaults.xsrfCookieName).toBe('csrftoken')
    expect(axios.defaults.xsrfHeaderName).toBe('X-CSRFToken')
    expect(axios.defaults.headers.get['Cache-Control']).toBe('no-cache, no-store, must-revalidate')
  })

  it('V2018-EST-036: monta as URLs sob /api/<app>/<model>/', () => {
    utils.getModel('loa', 'loa', 7)
    utils.getModelList('loa', 'loa', 2, '&ano=2026')
    utils.getModelOrderedList('loa', 'loa', '-ano', 3)
    utils.getModelAction('loa', 'loa', 7, 'espelho', 'a=1')

    expect(axios.mock.calls.map(chamada => chamada[0])).toEqual([
      { url: '/api/loa/loa/7/', method: 'GET' },
      { url: '/api/loa/loa/?page=2&ano=2026', method: 'GET' },
      { url: '/api/loa/loa/?o=-ano&page=3', method: 'GET' },
      { url: '/api/loa/loa/7/espelho/?a=1', method: 'GET' }
    ])
  })

  it('V2018-EST-036: fetch monta a URL a partir de app, model, id, action e params', () => {
    utils.fetch({ app: 'loa', model: 'loa' })
    utils.fetch({ app: 'loa', model: 'loa', id: 7, action: 'espelho', params: { a: 1, b: 'x' } })

    expect(axios.mock.calls.map(chamada => chamada[0].url)).toEqual([
      '/api/loa/loa/',
      '/api/loa/loa/7/espelho/?a=1&b=x'
    ])
  })

  it('V2018-EST-036: escritas usam post, patch e delete do axios', () => {
    utils.postModel('loa', 'loa', { a: 1 })
    utils.patchModel('loa', 'loa', 7, { a: 2 })
    utils.deleteModel('loa', 'loa', 7)

    expect(axios.post).toHaveBeenCalledWith('/api/loa/loa/', { a: 1 })
    expect(axios.patch).toHaveBeenCalledWith('/api/loa/loa/7/', { a: 2 })
    expect(axios.delete).toHaveBeenCalledWith('/api/loa/loa/7/')
  })
})
