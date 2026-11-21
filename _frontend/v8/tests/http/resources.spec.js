import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import pinia from '~@/core/pinia'
import { HttpError } from '~@/http/client'
import { reiniciarFluxoDeSessao } from '~@/http/sessao'
import { useGlobalStore } from '~@/stores/GlobalStore'
import Resources from '~@/utils/resources'

import { chamada, definirCookie, erroDe, respostaJson, respostaVazia, simularFetch } from './apoio'

vi.mock('~@/core/navegacao', () => ({
  ir: vi.fn(),
  recarregar: vi.fn(),
  abrirNovaAba: vi.fn(),
  caminhoAtual: vi.fn(() => '/v8/demo/')
}))

const Utils = Resources.Utils

describe('Resources.Utils', () => {
  beforeEach(() => {
    useGlobalStore(pinia).$reset()
    reiniciarFluxoDeSessao()
    definirCookie('csrftoken', 'token-1')
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('V8-HTTP-030: mantém as funções atuais, menos o login por senha', () => {
    expect(Object.keys(Utils).sort()).toEqual([
      'deleteModel', 'fetch', 'getVersion', 'hasPermission', 'logout', 'patchModel', 'postModel', 'putModel'
    ])
  })

  it('V8-HTTP-030: fetch monta a URL de app, model, id e action e responde { data }', async () => {
    const fetch = simularFetch(() => respostaJson({ id: 5, nome: 'x' }))
    const resposta = await Utils.fetch({ app: 'materia', model: 'materialegislativa', id: 5, action: 'ultimas' })
    expect(resposta).toEqual({ data: { id: 5, nome: 'x' } })
    const { url, init } = chamada(fetch)
    expect(url.pathname).toBe('/api/materia/materialegislativa/5/ultimas/')
    expect(url.search).toBe('')
    expect(init.method).toBe('GET')
  })

  it('V8-HTTP-030: fetch transforma params em query string e a guarda em m.query_string', async () => {
    const fetch = simularFetch(() => respostaJson({ results: [] }))
    const m = { app: 'sessao', model: 'sessaoplenaria', params: { page: 2, o: 'id', ano: '2024,2025' } }
    await Utils.fetch(m)
    const { url } = chamada(fetch)
    expect(url.pathname).toBe('/api/sessao/sessaoplenaria/')
    expect(url.searchParams.get('page')).toBe('2')
    expect(url.searchParams.get('o')).toBe('id')
    expect(url.searchParams.get('ano')).toBe('2024,2025')
    expect(m.query_string).toBe('page=2&o=id&ano=2024%2C2025')
  })

  it('V8-HTTP-030: fetch usa query_string pronta e o método informado', async () => {
    const fetch = simularFetch(() => respostaJson({}))
    await Utils.fetch({ app: 'norma', model: 'normajuridica', query_string: 'tipo=3', params: { ignorado: 1 } }, 'OPTIONS')
    const { url, init } = chamada(fetch)
    expect(url.search).toBe('?tipo=3')
    expect(init.method).toBe('OPTIONS')
  })

  it('V8-HTTP-030: GET não usa cache do navegador nem manda os cabeçalhos no-cache antigos', async () => {
    const fetch = simularFetch(() => respostaJson({}))
    await Utils.fetch({ app: 'norma', model: 'normajuridica' })
    await Utils.getVersion()
    fetch.mock.calls.forEach(([, init]) => {
      expect(init.cache).toBe('no-store')
      expect(init.headers.has('Cache-Control')).toBe(false)
      expect(init.headers.has('Pragma')).toBe(false)
      expect(init.headers.has('Expires')).toBe(false)
    })
  })

  it('V8-HTTP-030: patchModel, putModel e postModel enviam o form e respondem { data }', async () => {
    const fetch = simularFetch((url, init) => respostaJson({ metodo: init.method }))
    const m = { app: 'loa', model: 'emendaloa', id: 9, action: 'updatevalor', form: { valor: '10,00' }, progress: { onUploadProgress: () => {} } }
    expect(await Utils.patchModel(m)).toEqual({ data: { metodo: 'PATCH' } })
    expect(await Utils.putModel(m)).toEqual({ data: { metodo: 'PUT' } })
    expect(await Utils.postModel(m)).toEqual({ data: { metodo: 'POST' } })
    expect(chamada(fetch, 0).url.pathname).toBe('/api/loa/emendaloa/9/updatevalor/')
    expect(chamada(fetch, 1).url.pathname).toBe('/api/loa/emendaloa/9/updatevalor/')
    // postModel nunca leva o id na URL.
    expect(chamada(fetch, 2).url.pathname).toBe('/api/loa/emendaloa/updatevalor/')
    fetch.mock.calls.forEach(([, init]) => {
      expect(JSON.parse(init.body)).toEqual({ valor: '10,00' })
      expect(init.headers.get('Content-Type')).toBe('application/json')
      expect(init.headers.get('X-CSRFToken')).toBe('token-1')
    })
  })

  it('V8-HTTP-030: sem form, envia objeto vazio; FormData vai como está', async () => {
    const fetch = simularFetch(() => respostaJson({}))
    await Utils.postModel({ app: 'arq', model: 'arqdoc' })
    const form = new FormData()
    form.append('arquivo', 'x')
    await Utils.patchModel({ app: 'arq', model: 'arqdoc', id: 1, form })
    expect(chamada(fetch, 0).url.pathname).toBe('/api/arq/arqdoc/')
    expect(chamada(fetch, 0).init.body).toBe('{}')
    expect(chamada(fetch, 1).init.body).toBe(form)
    expect(chamada(fetch, 1).headers.has('Content-Type')).toBe(false)
  })

  it('V8-HTTP-030: deleteModel chama DELETE no registro e responde { data: null } em 204', async () => {
    const fetch = simularFetch(() => respostaVazia(204))
    expect(await Utils.deleteModel({ app: 'loa', model: 'emendaloa', id: 9 })).toEqual({ data: null })
    const { url, init } = chamada(fetch)
    expect(url.pathname).toBe('/api/loa/emendaloa/9/')
    expect(init.method).toBe('DELETE')
    expect(init.headers.get('X-CSRFToken')).toBe('token-1')
  })

  it('V8-HTTP-030: getVersion e logout usam os endereços dos dados globais', async () => {
    const fetch = simularFetch(() => respostaJson({ detail: 'ok' }))
    expect(await Utils.getVersion()).toEqual({ data: { detail: 'ok' } })
    expect(await Utils.logout()).toEqual({ data: { detail: 'ok' } })
    expect(chamada(fetch, 0).url.pathname).toBe('/api/version')
    expect(chamada(fetch, 0).init.method).toBe('GET')
    expect(chamada(fetch, 1).url.pathname).toBe('/api/auth/session')
    expect(chamada(fetch, 1).init.method).toBe('DELETE')
    expect(chamada(fetch, 1).init.body).toBeUndefined()
  })

  it('V8-HTTP-030: hasPermission usa OPTIONS e responde true, false ou false em caso de erro', async () => {
    let resposta = () => respostaJson({ status: 'ok' })
    const fetch = simularFetch(() => resposta())
    expect(await Utils.hasPermission('materia.add_materialegislativa')).toBe(true)
    const { url, init } = chamada(fetch)
    expect(init.method).toBe('OPTIONS')
    expect(url.pathname).toBe('/api/auth/session')
    expect(url.searchParams.get('perm')).toBe('materia.add_materialegislativa')

    resposta = () => respostaJson({ status: 'fail' })
    expect(await Utils.hasPermission('x.y')).toBe(false)

    vi.spyOn(console, 'warn').mockImplementation(() => {})
    resposta = () => respostaJson({ detail: 'erro' }, 500)
    expect(await Utils.hasPermission('x.y')).toBe(false)
  })

  it('V8-HTTP-030: erro rejeita com HttpError', async () => {
    simularFetch(() => respostaJson({ nome: ['Obrigatório.'] }, 400))
    const erro = await erroDe(Utils.postModel({ app: 'loa', model: 'emendaloa', form: {} }))
    expect(erro).toBeInstanceOf(HttpError)
    expect(erro.codigo).toBe('validacao')
    expect(erro.campos).toEqual({ nome: ['Obrigatório.'] })
  })
})
