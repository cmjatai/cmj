import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import pinia from '~@/core/pinia'
import http, { HttpError } from '~@/http/client'
import { reiniciarFluxoDeSessao } from '~@/http/sessao'
import { useOverlayStore } from '~@/overlays/OverlayStore'
import { useAuthStore } from '~@/stores/AuthStore'
import { useGlobalStore } from '~@/stores/GlobalStore'

import { chamada, definirCookie, erroDe, respostaHtml, respostaJson, respostaVazia, simularFetch } from './apoio'

vi.mock('~@/core/navegacao', () => ({
  ir: vi.fn(),
  recarregar: vi.fn(),
  abrirNovaAba: vi.fn(),
  caminhoAtual: vi.fn(() => '/v8/demo/?pagina=2')
}))

const ORIGEM = window.location.origin

describe('cliente HTTP', () => {
  beforeEach(() => {
    useGlobalStore(pinia).$reset()
    useAuthStore(pinia).$reset()
    useOverlayStore(pinia).$limpar()
    reiniciarFluxoDeSessao()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('V8-HTTP-001: expõe get, post, put, patch, delete e request', async () => {
    const fetch = simularFetch(() => respostaJson({ ok: true }))
    await http.get('/api/a')
    await http.post('/api/a', { x: 1 })
    await http.put('/api/a', { x: 1 })
    await http.patch('/api/a', { x: 1 })
    await http.delete('/api/a')
    await http.request('options', '/api/a')
    expect(fetch.mock.calls.map(([, init]) => init.method)).toEqual(['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'])
  })

  it('V8-HTTP-002: envia cookies só para a mesma origem', async () => {
    const fetch = simularFetch()
    await http.get('/api/a')
    const { url, init } = chamada(fetch)
    expect(url.href).toBe(`${ORIGEM}/api/a`)
    expect(init.credentials).toBe('same-origin')
    expect(init.mode).toBe('same-origin')
  })

  it('V8-HTTP-002: corpo em objeto vai como JSON', async () => {
    const fetch = simularFetch()
    await http.post('/api/a', { nome: 'Ana', itens: [1, 2] })
    const { init, headers } = chamada(fetch)
    expect(headers.get('Content-Type')).toBe('application/json')
    expect(JSON.parse(init.body)).toEqual({ nome: 'Ana', itens: [1, 2] })
  })

  it('V8-HTTP-002: request() aceita o corpo em opcoes.corpo', async () => {
    const fetch = simularFetch()
    await http.request('PUT', '/api/a', { corpo: { nome: 'Ana' } })
    expect(JSON.parse(chamada(fetch).init.body)).toEqual({ nome: 'Ana' })
  })

  it('V8-HTTP-002: FormData vai como está, sem Content-Type', async () => {
    const fetch = simularFetch()
    const form = new FormData()
    form.append('arquivo', 'conteúdo')
    await http.post('/api/a', form, { headers: { 'Content-Type': 'multipart/form-data' } })
    const { init, headers } = chamada(fetch)
    expect(init.body).toBe(form)
    expect(headers.has('Content-Type')).toBe(false)
  })

  it('V8-HTTP-002: requisição sem corpo não leva body nem Content-Type', async () => {
    const fetch = simularFetch()
    await http.get('/api/a')
    await http.post('/api/a')
    expect(chamada(fetch, 0).init.body).toBeUndefined()
    expect(chamada(fetch, 1).init.body).toBeUndefined()
    expect(chamada(fetch, 1).headers.has('Content-Type')).toBe(false)
  })

  it('V8-HTTP-002: params vira query string, repetindo a chave de listas e pulando nulos', async () => {
    const fetch = simularFetch()
    await http.get('/api/a?fixo=1', { params: { q: 'lei orgânica', ano: [2024, 2025], vazio: null, indefinido: undefined, zero: 0 } })
    const { url } = chamada(fetch)
    expect(url.pathname).toBe('/api/a')
    expect(url.searchParams.get('fixo')).toBe('1')
    expect(url.searchParams.get('q')).toBe('lei orgânica')
    expect(url.searchParams.getAll('ano')).toEqual(['2024', '2025'])
    expect(url.searchParams.get('zero')).toBe('0')
    expect(url.searchParams.has('vazio')).toBe(false)
    expect(url.searchParams.has('indefinido')).toBe(false)
  })

  it('V8-HTTP-002: GET não usa o cache do navegador', async () => {
    const fetch = simularFetch()
    await http.get('/api/a')
    await http.post('/api/a', {})
    expect(chamada(fetch, 0).init.cache).toBe('no-store')
    expect(chamada(fetch, 1).init.cache).toBeUndefined()
  })

  it('V8-HTTP-003: envia X-CSRFToken lido do cookie em POST, PUT, PATCH e DELETE', async () => {
    const fetch = simularFetch()
    definirCookie('outro', 'x')
    definirCookie('csrftoken', 'token-1')
    await http.post('/api/a', {})
    await http.put('/api/a', {})
    await http.patch('/api/a', {})
    await http.delete('/api/a')
    await http.get('/api/a')
    await http.request('OPTIONS', '/api/a')
    const tokens = fetch.mock.calls.map(([, init]) => init.headers.get('X-CSRFToken'))
    expect(tokens).toEqual(['token-1', 'token-1', 'token-1', 'token-1', null, null])
  })

  it('V8-HTTP-003: o cookie é lido no momento de cada requisição', async () => {
    const fetch = simularFetch()
    definirCookie('csrftoken', 'antes-do-login')
    await http.post('/api/a', {})
    definirCookie('csrftoken', 'depois-do-login')
    await http.post('/api/a', {})
    expect(chamada(fetch, 0).headers.get('X-CSRFToken')).toBe('antes-do-login')
    expect(chamada(fetch, 1).headers.get('X-CSRFToken')).toBe('depois-do-login')
  })

  it('V8-HTTP-003: sem o cookie, o cabeçalho não é enviado', async () => {
    const fetch = simularFetch()
    await http.post('/api/a', {}, { headers: { 'X-CSRFToken': 'forjado' } })
    expect(chamada(fetch).headers.has('X-CSRFToken')).toBe(false)
  })

  it('V8-HTTP-005: toda requisição leva X-Requested-With e Accept de JSON', async () => {
    const fetch = simularFetch()
    await http.get('/api/a')
    await http.post('/api/a', {})
    fetch.mock.calls.forEach(([, init]) => {
      expect(init.headers.get('X-Requested-With')).toBe('XMLHttpRequest')
      expect(init.headers.get('Accept')).toBe('application/json')
    })
  })

  it('V8-HTTP-005: accept html pede text/html e mantém os cabeçalhos de quem chama', async () => {
    const fetch = simularFetch(() => respostaHtml('<p>oi</p>'))
    await http.get('/v8/_frag/demo/', { accept: 'html', headers: { 'X-V8-Frag': '1' } })
    const { headers } = chamada(fetch)
    expect(headers.get('Accept')).toBe('text/html')
    expect(headers.get('X-Requested-With')).toBe('XMLHttpRequest')
    expect(headers.get('X-V8-Frag')).toBe('1')
  })

  it('V8-HTTP-006: JSON volta convertido, HTML volta como texto e 204 volta null', async () => {
    simularFetch(url => {
      if (url.pathname === '/json') {
        return respostaJson({ id: 3, nomes: ['a'] })
      }
      if (url.pathname === '/html') {
        return respostaHtml('<p>fragmento</p>')
      }
      if (url.pathname === '/vazio') {
        return new Response('', { status: 200, headers: { 'Content-Type': 'application/json' } })
      }
      return respostaVazia(204)
    })
    expect(await http.get('/json')).toEqual({ id: 3, nomes: ['a'] })
    expect(await http.get('/html', { accept: 'html' })).toBe('<p>fragmento</p>')
    expect(await http.delete('/sem-conteudo')).toBeNull()
    expect(await http.get('/vazio')).toBeNull()
  })

  it('V8-HTTP-006: JSON ilegível em resposta de sucesso rejeita com código rede', async () => {
    simularFetch(() => new Response('{quebrado', { status: 200, headers: { 'Content-Type': 'application/json' } }))
    const erro = await erroDe(http.get('/api/a'))
    expect(erro).toBeInstanceOf(HttpError)
    expect(erro.codigo).toBe('rede')
  })

  it('V8-HTTP-007: requisição cancelada rejeita com código cancelada', async () => {
    const controle = new AbortController()
    const fetch = vi.fn((url, init) => new Promise((resolver, rejeitar) => {
      init.signal.addEventListener('abort', () => rejeitar(new DOMException('Abortada', 'AbortError')))
    }))
    vi.stubGlobal('fetch', fetch)
    const aviso = vi.spyOn(console, 'warn').mockImplementation(() => {})
    const falha = vi.spyOn(console, 'error').mockImplementation(() => {})
    const promessa = http.get('/api/a', { signal: controle.signal })
    await Promise.resolve()
    expect(chamada(fetch).init.signal).toBe(controle.signal)
    controle.abort()
    const erro = await erroDe(promessa)
    expect(erro).toBeInstanceOf(HttpError)
    expect(erro.codigo).toBe('cancelada')
    // Não gera aviso: nada no console e nenhum overlay.
    expect(aviso).not.toHaveBeenCalled()
    expect(falha).not.toHaveBeenCalled()
    expect(useOverlayStore(pinia).entradas).toEqual([])
  })

  it('V8-HTTP-007: sinal já cancelado nem chega ao fetch', async () => {
    const fetch = simularFetch()
    const controle = new AbortController()
    controle.abort()
    const erro = await erroDe(http.post('/api/a', {}, { signal: controle.signal }))
    expect(erro.codigo).toBe('cancelada')
    expect(fetch).not.toHaveBeenCalled()
  })

  it('V8-HTTP-010: toda falha rejeita com HttpError completo', async () => {
    vi.spyOn(console, 'warn').mockImplementation(() => {})
    simularFetch(() => respostaJson({ detail: 'Corrija os campos.', errors: { nome: ['Obrigatório.'] }, non_field_errors: ['Datas invertidas.'] }, 400))
    const erro = await erroDe(http.post('/v8/demo/', { nome: '' }))
    expect(erro).toBeInstanceOf(HttpError)
    expect(erro).toBeInstanceOf(Error)
    expect(erro.status).toBe(400)
    expect(erro.codigo).toBe('validacao')
    expect(erro.mensagem).toBe('Corrija os campos.')
    expect(erro.campos).toEqual({ nome: ['Obrigatório.'] })
    expect(erro.gerais).toEqual(['Datas invertidas.'])
    expect(erro.resposta).toEqual({ detail: 'Corrija os campos.', errors: { nome: ['Obrigatório.'] }, non_field_errors: ['Datas invertidas.'] })
  })

  it('V8-HTTP-010: falha do fetch rejeita com HttpError de código rede', async () => {
    vi.spyOn(console, 'warn').mockImplementation(() => {})
    vi.stubGlobal('fetch', vi.fn(() => Promise.reject(new TypeError('Failed to fetch'))))
    const erro = await erroDe(http.get('/api/a'))
    expect(erro).toBeInstanceOf(HttpError)
    expect(erro.codigo).toBe('rede')
    expect(erro.status).toBe(0)
    expect(erro.campos).toEqual({})
    expect(erro.gerais).toEqual([])
    expect(erro.resposta).toBeNull()
  })

  it('V8-HTTP-011: o código acompanha o status da resposta', async () => {
    vi.spyOn(console, 'warn').mockImplementation(() => {})
    const casos = {
      400: 'validacao',
      422: 'validacao',
      404: 'nao_encontrado',
      409: 'conflito',
      500: 'servidor',
      502: 'servidor',
      405: 'rede',
      429: 'rede'
    }
    simularFetch(url => respostaJson({}, Number(url.pathname.slice(1))))
    for (const status of Object.keys(casos)) {
      const erro = await erroDe(http.get(`/${status}`))
      expect(erro.status).toBe(Number(status))
      expect(erro.codigo).toBe(casos[status])
    }
  })

  it('V8-HTTP-011: 401 em página anônima é nao_autenticado', async () => {
    simularFetch(() => respostaJson({ detail: 'Sessão encerrada.' }, 401))
    const erro = await erroDe(http.get('/api/a'))
    expect(erro.codigo).toBe('nao_autenticado')
    expect(erro.status).toBe(401)
  })

  it('V8-HTTP-011: 403 com usuário autenticado é sem_permissao', async () => {
    simularFetch(url => (url.pathname === '/api/version'
      ? respostaJson({ is_authenticated: true, user: { id: 1 } })
      : respostaJson({ detail: 'Você não pode fazer isso.' }, 403)))
    const erro = await erroDe(http.get('/api/a'))
    expect(erro.codigo).toBe('sem_permissao')
    expect(erro.mensagem).toBe('Você não pode fazer isso.')
  })

  it('V8-HTTP-014: o cliente não mostra aviso por conta própria', async () => {
    vi.spyOn(console, 'warn').mockImplementation(() => {})
    const alerta = vi.fn()
    vi.stubGlobal('alert', alerta)
    const overlay = useOverlayStore(pinia)
    const abrir = vi.spyOn(overlay, 'abrir')
    const antes = document.body.innerHTML
    simularFetch(url => respostaJson({ detail: 'Falhou.' }, Number(url.pathname.slice(1))))
    for (const status of [400, 404, 409, 500]) {
      await erroDe(http.post(`/${status}`, { a: 1 }))
    }
    vi.stubGlobal('fetch', vi.fn(() => Promise.reject(new TypeError('Failed to fetch'))))
    await erroDe(http.get('/api/a'))
    expect(abrir).not.toHaveBeenCalled()
    expect(overlay.entradas).toEqual([])
    expect(alerta).not.toHaveBeenCalled()
    expect(document.body.innerHTML).toBe(antes)
  })

  it('V8-HTTP-040: recusa URL de outra origem sem chamar o fetch', async () => {
    vi.spyOn(console, 'warn').mockImplementation(() => {})
    const fetch = simularFetch()
    definirCookie('csrftoken', 'token-1')
    const urls = [
      'https://exemplo.invalid/api/a',
      '//exemplo.invalid/api/a',
      `${ORIGEM.replace('http:', 'https:')}/api/a`,
      `${ORIGEM}0/api/a`,
      'javascript:alert(1)',
      'data:application/json,{}'
    ]
    for (const url of urls) {
      const erro = await erroDe(http.post(url, { a: 1 }))
      expect(erro).toBeInstanceOf(HttpError)
      expect(erro.codigo).toBe('rede')
    }
    expect(fetch).not.toHaveBeenCalled()
  })

  it('V8-HTTP-040: aceita URL absoluta da própria origem', async () => {
    const fetch = simularFetch()
    await http.get(`${ORIGEM}/api/a`)
    expect(chamada(fetch).url.href).toBe(`${ORIGEM}/api/a`)
  })

  it('V8-HTTP-040: <base> apontando para fora não desvia a requisição', async () => {
    vi.spyOn(console, 'warn').mockImplementation(() => {})
    const fetch = simularFetch()
    const base = document.createElement('base')
    base.href = 'https://exemplo.invalid/'
    document.head.appendChild(base)
    try {
      const erro = await erroDe(http.post('api/a', { a: 1 }))
      expect(erro.codigo).toBe('rede')
      expect(fetch).not.toHaveBeenCalled()
    } finally {
      base.remove()
    }
  })

  it('V8-HTTP-045: o que vai para o console não inclui o corpo da requisição', async () => {
    const metodos = ['log', 'info', 'debug', 'warn', 'error']
    const espioes = metodos.map(nome => vi.spyOn(console, nome).mockImplementation(() => {}))
    const segredo = 'valor-que-nao-pode-vazar'
    const form = new FormData()
    form.append('campo', segredo)

    simularFetch(() => respostaJson({ detail: 'Falhou.', eco: segredo }, 500))
    await erroDe(http.post('/api/a', { campo: segredo }, { params: { q: segredo } }))
    await erroDe(http.put('/api/a', form))
    simularFetch(() => respostaJson({ campo: ['Inválido.'] }, 400))
    await erroDe(http.patch('/api/a', { campo: segredo }))
    vi.stubGlobal('fetch', vi.fn(() => Promise.reject(new TypeError('Failed to fetch'))))
    const erro = await erroDe(http.post('/api/a', { campo: segredo }))

    const registrado = espioes.flatMap(espiao => espiao.mock.calls.flat())
    // Falha de servidor e de rede é registrada, mas só com método, caminho e código.
    expect(registrado.length).toBeGreaterThan(0)
    registrado.forEach(item => {
      expect(typeof item).toBe('string')
      expect(item).not.toContain(segredo)
    })
    // O erro entregue a quem chamou também não carrega o que foi enviado.
    expect(JSON.stringify(erro)).not.toContain(segredo)
    expect(erro.message).not.toContain(segredo)
  })
})
