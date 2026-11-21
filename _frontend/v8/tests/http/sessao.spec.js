import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { caminhoAtual, ir, recarregar } from '~@/core/navegacao'
import pinia from '~@/core/pinia'
import http, { HttpError } from '~@/http/client'
import { reiniciarFluxoDeSessao } from '~@/http/sessao'
import { useOverlayStore } from '~@/overlays/OverlayStore'
import { useAuthStore } from '~@/stores/AuthStore'
import { useGlobalStore } from '~@/stores/GlobalStore'

import { assentar, chamadasPara, definirCookie, erroDe, respostaJson, simularFetch } from './apoio'

vi.mock('~@/core/navegacao', () => ({
  ir: vi.fn(),
  recarregar: vi.fn(),
  abrirNovaAba: vi.fn(),
  caminhoAtual: vi.fn()
}))

const USUARIO = { id: 7, username: 'ana', nome: 'Ana Souza', avatar: '/media/ana.png' }
const VERSAO_ANA = {
  version: 'v8',
  is_authenticated: true,
  permissions: ['materia.add_materialegislativa', 'norma.change_normajuridica'],
  user: { id: 7, username: 'ana', fullname: 'Ana Souza', avatar: '/media/ana.png' }
}
const VERSAO_ANONIMA = { version: 'v8' }

let global = null
let overlay = null
let auth = null
let abrirModal = null
let fecharModal = null
let servidor = null

// Servidor de mentira: sem sessão responde `statusSemSessao` a tudo, menos a /api/version.
function ligarServidor() {
  servidor = {
    logado: false,
    statusSemSessao: 401,
    versao: VERSAO_ANONIMA,
    falharVersao: false
  }
  servidor.fetch = simularFetch((url, init) => {
    if (url.pathname === '/api/version') {
      if (servidor.falharVersao) {
        throw new TypeError('Failed to fetch')
      }
      return respostaJson(servidor.versao)
    }
    if (!servidor.logado) {
      return respostaJson({ detail: 'As credenciais de autenticação não foram fornecidas.' }, servidor.statusSemSessao)
    }
    return respostaJson({ caminho: url.pathname, metodo: init.method })
  })
}

function entrarNoServidor(versao = VERSAO_ANA) {
  servidor.logado = true
  servidor.versao = versao
}

function paginaAutenticada() {
  global.$patch({ autenticado: true, usuario: { ...USUARIO }, permissoes: ['materia.add_materialegislativa'] })
  auth.hidratar()
}

// Acompanha uma promessa sem esperar por ela.
function acompanhar(promessa) {
  const estado = { situacao: 'pendente', valor: undefined, erro: undefined }
  promessa.then(
    valor => Object.assign(estado, { situacao: 'resolvida', valor }),
    erro => Object.assign(estado, { situacao: 'rejeitada', erro })
  )
  return estado
}

describe('sessão expirada', () => {
  beforeEach(() => {
    global = useGlobalStore(pinia)
    overlay = useOverlayStore(pinia)
    auth = useAuthStore(pinia)
    global.$reset()
    auth.$reset()
    overlay.$limpar()
    reiniciarFluxoDeSessao()
    vi.clearAllMocks()
    vi.mocked(caminhoAtual).mockReturnValue('/v8/demo/?pagina=2')
    abrirModal = vi.spyOn(overlay, 'openModal').mockImplementation(() => new Promise(resolver => {
      fecharModal = resolver
    }))
    vi.spyOn(console, 'warn').mockImplementation(() => {})
    ligarServidor()
  })

  afterEach(() => {
    reiniciarFluxoDeSessao()
    vi.unstubAllGlobals()
  })

  it('V8-HTTP-020: 401 é sessão expirada, sem consultar /api/version', async () => {
    paginaAutenticada()
    const pedido = acompanhar(http.get('/api/materia/'))
    await assentar()
    expect(abrirModal).toHaveBeenCalledTimes(1)
    expect(pedido.situacao).toBe('pendente')
    expect(chamadasPara(servidor.fetch, '/api/version')).toHaveLength(0)
  })

  it('V8-HTTP-020: 403 seguido de /api/version sem usuário é sessão expirada', async () => {
    paginaAutenticada()
    servidor.statusSemSessao = 403
    const pedido = acompanhar(http.post('/api/materia/', { a: 1 }))
    await assentar()
    const consultas = chamadasPara(servidor.fetch, '/api/version')
    expect(consultas).toHaveLength(1)
    expect(consultas[0].init.method).toBe('GET')
    expect(abrirModal).toHaveBeenCalledTimes(1)
    expect(pedido.situacao).toBe('pendente')
  })

  it('V8-HTTP-020: 403 com usuário autenticado é sem_permissao e não abre modal', async () => {
    paginaAutenticada()
    servidor.statusSemSessao = 403
    servidor.versao = VERSAO_ANA
    const erro = await erroDe(http.delete('/api/materia/3/'))
    expect(erro).toBeInstanceOf(HttpError)
    expect(erro.codigo).toBe('sem_permissao')
    expect(erro.status).toBe(403)
    expect(abrirModal).not.toHaveBeenCalled()
    expect(ir).not.toHaveBeenCalled()
  })

  it('V8-HTTP-020: 403 sem resposta de /api/version continua sendo sem_permissao', async () => {
    paginaAutenticada()
    servidor.statusSemSessao = 403
    servidor.falharVersao = true
    const erro = await erroDe(http.get('/api/materia/'))
    expect(erro.codigo).toBe('sem_permissao')
    expect(abrirModal).not.toHaveBeenCalled()
  })

  it('V8-HTTP-020: a consulta a /api/version não entra no fluxo de sessão', async () => {
    paginaAutenticada()
    servidor.fetch = simularFetch(() => respostaJson({ detail: 'Negado.' }, 403))
    const erro = await erroDe(http.get('/api/materia/'))
    // /api/version também respondeu 403: uma única consulta, sem recursão e sem modal.
    expect(chamadasPara(servidor.fetch, '/api/version')).toHaveLength(1)
    expect(erro.codigo).toBe('sem_permissao')
    expect(abrirModal).not.toHaveBeenCalled()
  })

  it('V8-HTTP-021: abre o modal de reautenticação e deixa a requisição pendente', async () => {
    paginaAutenticada()
    const pedido = acompanhar(http.get('/api/materia/'))
    await assentar()
    expect(pedido.situacao).toBe('pendente')
    expect(abrirModal).toHaveBeenCalledTimes(1)
    const [carregador, props, opcoes] = abrirModal.mock.calls[0]
    expect(props).toEqual({})
    expect(opcoes).toEqual({ size: 'sm', title: 'Sessão expirada' })
    const modulo = await carregador()
    const ModalSessao = (await import('~@/http/ModalSessao.vue')).default
    expect(modulo.default).toBe(ModalSessao)
  })

  it('V8-HTTP-021: várias requisições com sessão expirada abrem um único modal', async () => {
    paginaAutenticada()
    const pedidos = [
      acompanhar(http.get('/api/materia/')),
      acompanhar(http.post('/api/norma/', { a: 1 })),
      acompanhar(http.patch('/api/sessao/4/', { b: 2 }))
    ]
    await assentar()
    servidor.statusSemSessao = 403
    pedidos.push(acompanhar(http.get('/api/parlamentares/')))
    await assentar()
    expect(abrirModal).toHaveBeenCalledTimes(1)
    expect(pedidos.map(p => p.situacao)).toEqual(['pendente', 'pendente', 'pendente', 'pendente'])
  })

  it('V8-HTTP-023: confirmada a sessão do mesmo usuário, cada pendente é refeita uma única vez', async () => {
    paginaAutenticada()
    definirCookie('csrftoken', 'antes')
    const pedidos = [
      acompanhar(http.get('/api/materia/')),
      acompanhar(http.post('/api/norma/', { a: 1 }))
    ]
    await assentar()
    expect(pedidos.map(p => p.situacao)).toEqual(['pendente', 'pendente'])

    entrarNoServidor()
    definirCookie('csrftoken', 'depois')
    fecharModal({ retomar: true, versao: VERSAO_ANA })
    await assentar()

    expect(pedidos[0]).toMatchObject({ situacao: 'resolvida', valor: { caminho: '/api/materia/', metodo: 'GET' } })
    expect(pedidos[1]).toMatchObject({ situacao: 'resolvida', valor: { caminho: '/api/norma/', metodo: 'POST' } })
    expect(chamadasPara(servidor.fetch, '/api/materia/')).toHaveLength(2)
    const posts = chamadasPara(servidor.fetch, '/api/norma/')
    expect(posts).toHaveLength(2)
    // A refeita é a mesma requisição, com o token CSRF que o login trocou.
    expect(posts[1].init.body).toBe(posts[0].init.body)
    expect(posts[0].headers.get('X-CSRFToken')).toBe('antes')
    expect(posts[1].headers.get('X-CSRFToken')).toBe('depois')
    expect(abrirModal).toHaveBeenCalledTimes(1)
    expect(ir).not.toHaveBeenCalled()
    expect(recarregar).not.toHaveBeenCalled()
  })

  it('V8-HTTP-023: a refeita envia o mesmo corpo, ainda que o objeto original tenha mudado', async () => {
    paginaAutenticada()
    const form = { valor: '10,00' }
    const pedido = acompanhar(http.patch('/api/loa/emendaloa/9/', form))
    await assentar()
    form.valor = '99,00'
    entrarNoServidor()
    fecharModal({ retomar: true, versao: VERSAO_ANA })
    await assentar()
    expect(pedido.situacao).toBe('resolvida')
    const envios = chamadasPara(servidor.fetch, '/api/loa/emendaloa/9/')
    expect(envios.map(c => JSON.parse(c.init.body))).toEqual([{ valor: '10,00' }, { valor: '10,00' }])
  })

  it('V8-HTTP-023: ao retomar, o AuthStore recebe os dados de /api/version', async () => {
    paginaAutenticada()
    expect(auth.permissions).toEqual(['materia.add_materialegislativa'])
    acompanhar(http.get('/api/materia/'))
    await assentar()
    entrarNoServidor()
    fecharModal({ retomar: true, versao: VERSAO_ANA })
    await assentar()
    expect(auth.isAuthenticated).toBe(true)
    expect(auth.permissions).toEqual(VERSAO_ANA.permissions)
    expect(auth.data_connect.user).toEqual(VERSAO_ANA.user)
  })

  it('V8-HTTP-023: segunda falha de sessão na mesma requisição rejeita com nao_autenticado', async () => {
    paginaAutenticada()
    const pedido = acompanhar(http.get('/api/materia/'))
    await assentar()
    // O modal diz que a sessão voltou, mas o servidor continua recusando.
    fecharModal({ retomar: true, versao: VERSAO_ANA })
    await assentar()
    expect(pedido.situacao).toBe('rejeitada')
    expect(pedido.erro).toBeInstanceOf(HttpError)
    expect(pedido.erro.codigo).toBe('nao_autenticado')
    expect(chamadasPara(servidor.fetch, '/api/materia/')).toHaveLength(2)
    expect(abrirModal).toHaveBeenCalledTimes(1)
  })

  it('V8-HTTP-023: segunda falha por 403 também rejeita com nao_autenticado, sem novo modal', async () => {
    paginaAutenticada()
    servidor.statusSemSessao = 403
    const pedido = acompanhar(http.get('/api/materia/'))
    await assentar()
    fecharModal({ retomar: true, versao: VERSAO_ANA })
    await assentar()
    expect(pedido.erro.codigo).toBe('nao_autenticado')
    expect(chamadasPara(servidor.fetch, '/api/materia/')).toHaveLength(2)
    expect(abrirModal).toHaveBeenCalledTimes(1)
  })

  it('V8-HTTP-023: uma nova requisição, depois de retomada a sessão, abre o modal de novo se preciso', async () => {
    paginaAutenticada()
    acompanhar(http.get('/api/materia/'))
    await assentar()
    entrarNoServidor()
    fecharModal({ retomar: true, versao: VERSAO_ANA })
    await assentar()
    servidor.logado = false
    const outra = acompanhar(http.get('/api/norma/'))
    await assentar()
    expect(outra.situacao).toBe('pendente')
    expect(abrirModal).toHaveBeenCalledTimes(2)
  })

  it('V8-HTTP-024: dispensar o modal rejeita as pendentes e leva ao login com retorno', async () => {
    paginaAutenticada()
    const pedidos = [acompanhar(http.get('/api/materia/')), acompanhar(http.post('/api/norma/', {}))]
    await assentar()
    fecharModal(undefined)
    await assentar()
    pedidos.forEach(pedido => {
      expect(pedido.situacao).toBe('rejeitada')
      expect(pedido.erro).toBeInstanceOf(HttpError)
      expect(pedido.erro.codigo).toBe('nao_autenticado')
    })
    expect(ir).toHaveBeenCalledTimes(1)
    expect(ir).toHaveBeenCalledWith('/login/?next=' + encodeURIComponent('/v8/demo/?pagina=2'))
    // Nada é refeito.
    expect(chamadasPara(servidor.fetch, '/api/materia/')).toHaveLength(1)
    expect(chamadasPara(servidor.fetch, '/api/norma/')).toHaveLength(1)
  })

  it('V8-HTTP-024: "Ir para o login" rejeita as pendentes e leva ao login', async () => {
    paginaAutenticada()
    global.urls.login = '/entrar/'
    const pedido = acompanhar(http.get('/api/materia/'))
    await assentar()
    fecharModal({ retomar: false })
    await assentar()
    expect(pedido.erro.codigo).toBe('nao_autenticado')
    expect(ir).toHaveBeenCalledWith('/entrar/?next=' + encodeURIComponent('/v8/demo/?pagina=2'))
    expect(recarregar).not.toHaveBeenCalled()
  })

  it('V8-HTTP-024: com alterações não salvas, pergunta antes de sair e fica se a resposta for não', async () => {
    paginaAutenticada()
    overlay.registrar({ id: 'painel-a', kind: 'drawer' })
    overlay.registrar({ id: 'painel-b', kind: 'drawer' })
    overlay.setDirty('painel-b', true)
    const guarda = vi.spyOn(overlay, 'podeDescartar').mockResolvedValue(false)
    const pedido = acompanhar(http.get('/api/materia/'))
    await assentar()
    fecharModal({ retomar: false })
    await assentar()
    expect(pedido.erro.codigo).toBe('nao_autenticado')
    expect(guarda).toHaveBeenCalledTimes(1)
    expect(guarda).toHaveBeenCalledWith(['painel-a', 'painel-b'])
    expect(ir).not.toHaveBeenCalled()
  })

  it('V8-HTTP-024: com alterações não salvas, sai quando o usuário aceita descartar', async () => {
    paginaAutenticada()
    overlay.registrar({ id: 'painel-a', kind: 'drawer' })
    overlay.setDirty('painel-a', true)
    const guarda = vi.spyOn(overlay, 'podeDescartar').mockResolvedValue(true)
    acompanhar(http.get('/api/materia/'))
    await assentar()
    fecharModal(undefined)
    await assentar()
    expect(guarda).toHaveBeenCalledWith(['painel-a'])
    expect(ir).toHaveBeenCalledTimes(1)
  })

  it('V8-HTTP-024: sem alterações, sai sem perguntar', async () => {
    paginaAutenticada()
    overlay.registrar({ id: 'painel-a', kind: 'drawer' })
    const guarda = vi.spyOn(overlay, 'podeDescartar')
    acompanhar(http.get('/api/materia/'))
    await assentar()
    fecharModal(undefined)
    await assentar()
    expect(guarda).not.toHaveBeenCalled()
    expect(ir).toHaveBeenCalledTimes(1)
  })

  it('V8-HTTP-024: falha de sessão enquanto a saída é confirmada rejeita sem abrir outro modal', async () => {
    paginaAutenticada()
    overlay.registrar({ id: 'painel-a', kind: 'drawer' })
    overlay.setDirty('painel-a', true)
    let responder = null
    vi.spyOn(overlay, 'podeDescartar').mockImplementation(() => new Promise(resolver => {
      responder = resolver
    }))
    acompanhar(http.get('/api/materia/'))
    await assentar()
    fecharModal({ retomar: false })
    await assentar()
    const erro = await erroDe(http.get('/api/norma/'))
    expect(erro.codigo).toBe('nao_autenticado')
    expect(abrirModal).toHaveBeenCalledTimes(1)
    // O usuário decide ficar: a próxima falha volta a abrir o modal.
    responder(false)
    await assentar()
    const outra = acompanhar(http.get('/api/norma/'))
    await assentar()
    expect(outra.situacao).toBe('pendente')
    expect(abrirModal).toHaveBeenCalledTimes(2)
  })

  it('V8-HTTP-025: em página carregada como anônimo, 401 rejeita com nao_autenticado sem modal', async () => {
    const erro = await erroDe(http.get('/api/materia/'))
    expect(erro).toBeInstanceOf(HttpError)
    expect(erro.codigo).toBe('nao_autenticado')
    expect(erro.status).toBe(401)
    expect(abrirModal).not.toHaveBeenCalled()
    expect(ir).not.toHaveBeenCalled()
    expect(chamadasPara(servidor.fetch, '/api/materia/')).toHaveLength(1)
  })

  it('V8-HTTP-025: em página anônima, 403 sem usuário também rejeita com nao_autenticado', async () => {
    servidor.statusSemSessao = 403
    const erro = await erroDe(http.post('/api/materia/', {}))
    expect(erro.codigo).toBe('nao_autenticado')
    expect(erro.status).toBe(403)
    expect(abrirModal).not.toHaveBeenCalled()
  })

  it('V8-HTTP-041: o retorno ao login vem só de caminhoAtual()', async () => {
    paginaAutenticada()
    vi.mocked(caminhoAtual).mockReturnValue('/v8/loa/emendas/?fase=10&q=a b')
    // Nada do que o servidor ou o modal informam entra no endereço de retorno.
    servidor.fetch = simularFetch(() => respostaJson({
      detail: 'Sessão encerrada.',
      next: 'https://exemplo.invalid/roubo',
      login_url: 'https://exemplo.invalid/login'
    }, 401))
    acompanhar(http.get('/api/materia/?next=https://exemplo.invalid/', { params: { next: '//exemplo.invalid' } }))
    await assentar()
    fecharModal({ retomar: false, next: 'https://exemplo.invalid/', url: 'https://exemplo.invalid/' })
    await assentar()
    expect(ir).toHaveBeenCalledTimes(1)
    const destino = new URL(vi.mocked(ir).mock.calls[0][0], window.location.origin)
    expect(destino.origin).toBe(window.location.origin)
    expect(destino.pathname).toBe('/login/')
    expect([...destino.searchParams.keys()]).toEqual(['next'])
    expect(destino.searchParams.get('next')).toBe('/v8/loa/emendas/?fase=10&q=a b')
    expect(vi.mocked(ir).mock.calls[0][0]).not.toContain('exemplo.invalid')
  })

  it('V8-HTTP-041: caminhoAtual() devolve só caminho e query, sem host', async () => {
    const real = await vi.importActual('~@/core/navegacao')
    window.history.replaceState(null, '', '/v8/demo/?pagina=3#topo')
    try {
      expect(real.caminhoAtual()).toBe('/v8/demo/?pagina=3')
    } finally {
      window.history.replaceState(null, '', '/')
    }
  })

  it('V8-HTTP-042: se outro usuário entrou, recarrega a página e não refaz nada', async () => {
    paginaAutenticada()
    const antes = { ...auth.data_connect }
    const pedidos = [acompanhar(http.get('/api/materia/')), acompanhar(http.post('/api/norma/', { a: 1 }))]
    await assentar()
    const outro = { ...VERSAO_ANA, user: { id: 8, username: 'beto', fullname: 'Beto', avatar: '' }, permissions: ['base.add_tudo'] }
    entrarNoServidor(outro)
    fecharModal({ retomar: true, versao: outro })
    await assentar()
    expect(recarregar).toHaveBeenCalledTimes(1)
    expect(ir).not.toHaveBeenCalled()
    pedidos.forEach(pedido => {
      expect(pedido.situacao).toBe('rejeitada')
      expect(pedido.erro.codigo).toBe('nao_autenticado')
    })
    expect(chamadasPara(servidor.fetch, '/api/materia/')).toHaveLength(1)
    expect(chamadasPara(servidor.fetch, '/api/norma/')).toHaveLength(1)
    // As permissões do outro usuário não entram nesta página.
    expect(auth.data_connect).toEqual(antes)
  })

  it('V8-HTTP-042: resposta sem usuário identificado também não retoma', async () => {
    paginaAutenticada()
    const pedido = acompanhar(http.get('/api/materia/'))
    await assentar()
    entrarNoServidor()
    fecharModal({ retomar: true, versao: { is_authenticated: true } })
    await assentar()
    expect(recarregar).toHaveBeenCalledTimes(1)
    expect(pedido.erro.codigo).toBe('nao_autenticado')
    expect(chamadasPara(servidor.fetch, '/api/materia/')).toHaveLength(1)
  })

  it('V8-HTTP-007: cancelar uma requisição pendente de reautenticação rejeita com cancelada', async () => {
    paginaAutenticada()
    const controle = new AbortController()
    const cancelada = acompanhar(http.get('/api/materia/', { signal: controle.signal }))
    const outra = acompanhar(http.get('/api/norma/'))
    await assentar()
    controle.abort()
    await assentar()
    expect(cancelada.situacao).toBe('rejeitada')
    expect(cancelada.erro.codigo).toBe('cancelada')
    expect(outra.situacao).toBe('pendente')
    // Ao retomar, só a que continua pendente é refeita.
    entrarNoServidor()
    fecharModal({ retomar: true, versao: VERSAO_ANA })
    await assentar()
    expect(outra.situacao).toBe('resolvida')
    expect(chamadasPara(servidor.fetch, '/api/materia/')).toHaveLength(1)
    expect(chamadasPara(servidor.fetch, '/api/norma/')).toHaveLength(2)
  })
})
