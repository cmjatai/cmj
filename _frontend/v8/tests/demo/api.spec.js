import { afterEach, describe, expect, it, vi } from 'vitest'
import { HttpError } from '~@/http/client'
import { reiniciarFluxoDeSessao } from '~@/http/sessao'
import * as api from '~@/modules/demo/api'
import { clienteDeExemplo, limparStores, paginaDeExemplo } from './apoio'

function respostaJson(corpo, status = 200) {
  return new Response(JSON.stringify(corpo), {
    status,
    headers: { 'Content-Type': 'application/json' }
  })
}

// Substitui o fetch. `responder(url, init)` devolve a Response de cada chamada.
function simularFetch(responder) {
  const simulado = vi.fn(async (url, init) => responder(new URL(url), init))
  vi.stubGlobal('fetch', simulado)
  return simulado
}

function chamada(simulado, indice = 0) {
  const [url, init] = simulado.mock.calls[indice]
  return { url: new URL(url), init }
}

async function rejeicaoDe(promessa) {
  try {
    await promessa
  } catch (erro) {
    return erro
  }
  throw new Error('a promessa deveria ter rejeitado')
}

describe('API da demonstração', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
    reiniciarFluxoDeSessao()
    limparStores()
  })

  it('V8-DEMO-020: listar busca a página pedida e não envia filtro vazio', async () => {
    const fetch = simularFetch(() => respostaJson(paginaDeExemplo()))
    const resultado = await api.listar({ q: 'ana', situacao: '', cidade: null, pagina: 2 })
    const { url, init } = chamada(fetch)
    expect(init.method).toBe('GET')
    expect(url.pathname).toBe('/v8/demo/api/clientes/')
    expect([...url.searchParams.entries()]).toEqual([['q', 'ana'], ['pagina', '2']])
    expect(resultado.itens).toHaveLength(2)
  })

  it('V8-DEMO-013: obter busca o cliente pelo id, e id inexistente rejeita com nao_encontrado', async () => {
    const fetch = simularFetch(url =>
      url.pathname === '/v8/demo/api/clientes/7/'
        ? respostaJson(clienteDeExemplo())
        : respostaJson({ detail: 'Cliente não encontrado.' }, 404)
    )
    expect((await api.obter(7)).nome).toBe('Glória Exemplo')
    expect(chamada(fetch).init.method).toBe('GET')

    const erro = await rejeicaoDe(api.obter(999))
    expect(erro).toBeInstanceOf(HttpError)
    expect(erro.codigo).toBe('nao_encontrado')
    expect(chamada(fetch, 1).url.pathname).toBe('/v8/demo/api/clientes/999/')
  })

  it('V8-DEMO-022: salvar envia PUT em JSON, e o 400 chega com erros de campo e gerais', async () => {
    const dados = { nome: 'Glória Exemplo', email: 'ana.exemplo@exemplo.invalid', cidade: 'Jataí', situacao: 'inativo', motivo: '' }
    const fetch = simularFetch(() => respostaJson({
      detail: 'Verifique os dados informados.',
      errors: { email: ['Este e-mail já é usado por outro cliente.'] },
      non_field_errors: ['Cliente inativo precisa de um motivo preenchido.']
    }, 400))
    const erro = await rejeicaoDe(api.salvar(7, dados))
    const { url, init } = chamada(fetch)
    expect(init.method).toBe('PUT')
    expect(url.pathname).toBe('/v8/demo/api/clientes/7/')
    expect(init.headers.get('Content-Type')).toBe('application/json')
    expect(JSON.parse(init.body)).toEqual(dados)
    expect(erro.codigo).toBe('validacao')
    expect(erro.campos).toEqual({ email: ['Este e-mail já é usado por outro cliente.'] })
    expect(erro.gerais).toEqual(['Cliente inativo precisa de um motivo preenchido.'])
  })

  it('V8-DEMO-023: criar envia POST em JSON e resolve com o cliente', async () => {
    const dados = { nome: 'Novo Modelo', email: 'novo.modelo@exemplo.invalid', cidade: 'Jataí', situacao: 'ativo', motivo: '' }
    const fetch = simularFetch(() => respostaJson({ id: 43, ...dados, desde: '2026-11-21', pedidos: [] }, 201))
    const criado = await api.criar(dados)
    const { url, init } = chamada(fetch)
    expect(init.method).toBe('POST')
    expect(url.pathname).toBe('/v8/demo/api/clientes/')
    expect(JSON.parse(init.body)).toEqual(dados)
    expect(criado.id).toBe(43)
  })

  it('V8-DEMO-025: negado rejeita com sem_permissao quando a sessão continua válida', async () => {
    const fetch = simularFetch(url =>
      url.pathname === '/v8/demo/api/negado/'
        ? respostaJson({ detail: 'Você não tem permissão para executar esta ação.' }, 403)
        : respostaJson({ is_authenticated: true, user: { id: 1 } })
    )
    const erro = await rejeicaoDe(api.negado())
    expect(chamada(fetch).init.method).toBe('GET')
    expect(chamada(fetch).url.pathname).toBe('/v8/demo/api/negado/')
    expect(erro).toBeInstanceOf(HttpError)
    expect(erro.status).toBe(403)
    expect(erro.codigo).toBe('sem_permissao')
    expect(erro.mensagem).toBe('Você não tem permissão para executar esta ação.')
  })
})
