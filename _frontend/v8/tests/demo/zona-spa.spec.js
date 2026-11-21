import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { h } from 'vue'
import { RouterView } from 'vue-router'
import { zonas } from '~@/core/zonas'
import { HttpError } from '~@/http/client'
import * as api from '~@/modules/demo/api'
import zona from '~@/modules/demo/zona'
import {
  PREFIXO,
  assentar,
  clienteDeExemplo,
  criarRouterDaZona,
  fecharOverlay,
  limparStores,
  overlaysAbertos,
  paginaDeExemplo,
  toasts
} from './apoio'

vi.mock('~@/modules/demo/api')

// Monta a zona inteira num router de verdade. `drawerRota: false` troca o <DrawerRota> por um
// substituto, para os testes que só olham a lista.
async function abrir(caminho, { drawerRota = false } = {}) {
  const router = criarRouterDaZona()
  router.push(caminho)
  await router.isReady()
  const wrapper = mount({ render: () => h(RouterView) }, {
    global: {
      plugins: [router],
      stubs: drawerRota ? {} : { DrawerRota: true }
    },
    attachTo: document.body
  })
  await assentar()
  return { wrapper, router }
}

function botao(wrapper, texto) {
  return wrapper.findAll('button').find(b => b.text() === texto)
}

function drawers() {
  return [...document.querySelectorAll('[data-overlay-kind="drawer"]')]
}

describe('rotas da zona SPA da demonstração', () => {
  it('V8-DEMO-020: o registro de zonas carrega este módulo, com layout e rotas', async () => {
    const modulo = await zonas['demo-spa']()
    expect(modulo.default).toBe(zona)
    expect(zona.layout).toBeTruthy()
    expect(Array.isArray(zona.rotas)).toBe(true)
  })

  it('V8-DEMO-020: a raiz da zona leva à lista de clientes', async () => {
    const router = criarRouterDaZona()
    await router.push(`${PREFIXO}/`)
    expect(router.currentRoute.value.name).toBe('demo_spa_clientes')
    expect(router.currentRoute.value.path).toBe(`${PREFIXO}/clientes`)
  })

  it('V8-DEMO-021: as três rotas têm nome e ficam sob o prefixo da zona', () => {
    const router = criarRouterDaZona()
    expect(router.resolve({ name: 'demo_spa_clientes' }).path).toBe(`${PREFIXO}/clientes`)
    expect(router.resolve({ name: 'demo_spa_cliente', params: { id: 7 } }).path).toBe(`${PREFIXO}/clientes/7`)
    expect(router.resolve({ name: 'demo_spa_pedido', params: { id: 7, pedido: 701 } }).path)
      .toBe(`${PREFIXO}/clientes/7/pedidos/701`)
    // Toda rota tem nome: o <DrawerRota> volta à rota pai pelo nome dela.
    router.getRoutes().forEach(rota => expect(rota.name).toBeTruthy())
  })

  it('V8-DEMO-021: o detalhe é rota filha da lista, e o pedido é rota filha do detalhe', () => {
    const router = criarRouterDaZona()
    const cliente = router.resolve(`${PREFIXO}/clientes/7`)
    expect(cliente.matched.map(r => r.name)).toEqual(['v8_zona_demo-spa', 'demo_spa_clientes', 'demo_spa_cliente'])
    const pedido = router.resolve(`${PREFIXO}/clientes/7/pedidos/701`)
    expect(pedido.matched.map(r => r.name)).toEqual([
      'v8_zona_demo-spa',
      'demo_spa_clientes',
      'demo_spa_cliente',
      'demo_spa_pedido'
    ])
  })

  it('V8-DEMO-021: as rotas filhas pedem drawer direito e entregam os ids como números', () => {
    const router = criarRouterDaZona()
    const rota = router.resolve(`${PREFIXO}/clientes/7/pedidos/701`)
    const [, lista, cliente, pedido] = rota.matched
    expect(lista.meta.drawer).toBeUndefined()
    expect(cliente.meta.drawer).toMatchObject({ side: 'right', size: 'md' })
    expect(pedido.meta.drawer).toMatchObject({ side: 'right', size: 'sm' })
    expect(cliente.props.default(rota)).toEqual({ id: 7 })
    expect(pedido.props.default(rota)).toEqual({ id: 7, pedido: 701 })
    expect(rota.matched.slice(1).map(r => r.meta.breadcrumb)).toEqual(['Clientes', 'Cliente', 'Pedido'])
  })

  it('V8-DEMO-021: id que não é número não casa com a rota do detalhe', () => {
    // O router avisa no console quando nada casa. No app, esses caminhos caem no 404 da zona.
    vi.spyOn(console, 'warn').mockImplementation(() => {})
    const router = criarRouterDaZona()
    expect(router.resolve(`${PREFIXO}/clientes/abc`).matched.map(r => r.name)).toEqual([])
    expect(router.resolve(`${PREFIXO}/clientes/7/pedidos/x`).matched.map(r => r.name)).toEqual([])
  })
})

describe('lista de clientes da zona SPA', () => {
  beforeEach(() => {
    api.listar.mockResolvedValue(paginaDeExemplo())
    api.obter.mockResolvedValue(clienteDeExemplo())
  })

  afterEach(limparStores)

  it('V8-DEMO-020: mostra o aviso de demonstração e os clientes vindos da API', async () => {
    const { wrapper } = await abrir(`${PREFIXO}/`)
    expect(api.listar).toHaveBeenCalledWith({ q: '', pagina: 1 })
    expect(wrapper.find('.v8-aviso-demo').text()).toContain('Nada do que for feito aqui é gravado.')
    expect(wrapper.find('h1.v8-pagina-titulo').exists()).toBe(true)

    const linhas = wrapper.findAll('table.v8-tabela tbody tr')
    expect(linhas).toHaveLength(2)
    expect(linhas[0].text()).toContain('Ana Exemplo')
    expect(linhas[0].text()).toContain('ana.exemplo@exemplo.invalid')
    expect(linhas[0].find('.v8-etiqueta-ok').text()).toBe('Ativo')
    expect(linhas[1].text()).toContain('Davi Exemplo')
    expect(linhas[1].find('.v8-etiqueta-neutra').text()).toBe('Inativo')
    expect(wrapper.text()).toContain('2 clientes encontrados.')
    expect(wrapper.find('nav.v8-paginacao').exists()).toBe(false)
    wrapper.unmount()
  })

  it('V8-DEMO-020: mostra o carregamento enquanto a API não responde', async () => {
    let responder
    api.listar.mockReturnValue(new Promise(resolver => {
      responder = resolver
    }))
    const { wrapper } = await abrir(`${PREFIXO}/clientes`)
    expect(wrapper.find('[role="status"]').text()).toBe('Carregando…')
    expect(wrapper.find('table').exists()).toBe(false)
    responder(paginaDeExemplo())
    await assentar()
    expect(wrapper.find('[role="status"]').exists()).toBe(false)
    expect(wrapper.find('table.v8-tabela').exists()).toBe(true)
    wrapper.unmount()
  })

  it('V8-DEMO-020: falha ao carregar mostra o erro e permite tentar de novo', async () => {
    api.listar.mockRejectedValueOnce(new HttpError({ status: 500, codigo: 'servidor' }))
    const { wrapper } = await abrir(`${PREFIXO}/clientes`)
    expect(wrapper.find('[role="alert"]').text()).toContain('O servidor encontrou um erro.')
    expect(wrapper.find('table').exists()).toBe(false)

    await botao(wrapper, 'Tentar de novo').trigger('click')
    await assentar()
    expect(wrapper.find('[role="alert"]').exists()).toBe(false)
    expect(wrapper.findAll('table.v8-tabela tbody tr')).toHaveLength(2)
    wrapper.unmount()
  })

  it('V8-DEMO-020: a busca espera a digitação parar e volta à primeira página', async () => {
    api.listar.mockResolvedValue(paginaDeExemplo({ total: 42, pagina: 3, paginas: 5 }))
    const { wrapper } = await abrir(`${PREFIXO}/clientes`)
    await botao(wrapper, 'Próxima').trigger('click')
    await assentar()
    api.listar.mockClear()

    vi.useFakeTimers()
    const busca = wrapper.find('input[type="search"]')
    await busca.setValue('an')
    await busca.setValue('ana ')
    await vi.advanceTimersByTimeAsync(200)
    expect(api.listar).not.toHaveBeenCalled()
    await vi.advanceTimersByTimeAsync(200)
    expect(api.listar).toHaveBeenCalledTimes(1)
    expect(api.listar).toHaveBeenCalledWith({ q: 'ana', pagina: 1 })
    wrapper.unmount()
  })

  it('V8-DEMO-020: Enter na busca não espera o atraso nem repete o pedido depois', async () => {
    const { wrapper } = await abrir(`${PREFIXO}/clientes`)
    api.listar.mockClear()
    vi.useFakeTimers()
    await wrapper.find('input[type="search"]').setValue('davi')
    await wrapper.find('form[role="search"]').trigger('submit')
    expect(api.listar).toHaveBeenCalledTimes(1)
    expect(api.listar).toHaveBeenCalledWith({ q: 'davi', pagina: 1 })
    await vi.advanceTimersByTimeAsync(1000)
    expect(api.listar).toHaveBeenCalledTimes(1)
    wrapper.unmount()
  })

  it('V8-DEMO-020: a paginação pede a página vizinha e desliga o botão no limite', async () => {
    api.listar.mockImplementation(async ({ pagina }) => paginaDeExemplo({ total: 15, pagina, paginas: 2 }))
    const { wrapper } = await abrir(`${PREFIXO}/clientes`)
    expect(wrapper.find('nav.v8-paginacao').text()).toContain('Página 1 de 2')
    expect(botao(wrapper, 'Anterior').element.disabled).toBe(true)

    await botao(wrapper, 'Próxima').trigger('click')
    await assentar()
    expect(api.listar).toHaveBeenLastCalledWith({ q: '', pagina: 2 })
    expect(wrapper.find('nav.v8-paginacao').text()).toContain('Página 2 de 2')
    expect(botao(wrapper, 'Próxima').element.disabled).toBe(true)

    await botao(wrapper, 'Anterior').trigger('click')
    await assentar()
    expect(api.listar).toHaveBeenLastCalledWith({ q: '', pagina: 1 })
    wrapper.unmount()
  })

  it('V8-DEMO-020: resposta de uma busca antiga não substitui a da mais nova', async () => {
    const pendentes = []
    api.listar.mockImplementation(() => new Promise(resolver => pendentes.push(resolver)))
    const { wrapper } = await abrir(`${PREFIXO}/clientes`)
    await wrapper.find('input[type="search"]').setValue('davi')
    await wrapper.find('form[role="search"]').trigger('submit')
    expect(pendentes).toHaveLength(2)

    const [ana, davi] = paginaDeExemplo().itens
    pendentes[1](paginaDeExemplo({ total: 1, itens: [davi] }))
    await assentar()
    pendentes[0](paginaDeExemplo({ total: 1, itens: [ana] }))
    await assentar()
    const linhas = wrapper.findAll('table.v8-tabela tbody tr')
    expect(linhas).toHaveLength(1)
    expect(linhas[0].text()).toContain('Davi Exemplo')
    wrapper.unmount()
  })

  it('V8-DEMO-021: o nome de cada cliente leva à rota aninhada do detalhe', async () => {
    const { wrapper, router } = await abrir(`${PREFIXO}/clientes`)
    const links = wrapper.findAll('table.v8-tabela tbody a')
    expect(links.map(a => a.attributes('href'))).toEqual([`${PREFIXO}/clientes/1`, `${PREFIXO}/clientes/4`])

    await links[1].trigger('click')
    await assentar()
    expect(router.currentRoute.value.name).toBe('demo_spa_cliente')
    expect(router.currentRoute.value.params.id).toBe('4')
    // A lista continua na tela: o detalhe é desenhado por cima dela.
    expect(wrapper.findAll('table.v8-tabela tbody tr')).toHaveLength(2)
    wrapper.unmount()
  })

  it('V8-DEMO-021: abrir a URL do detalhe mostra o drawer do cliente sobre a lista', async () => {
    const { wrapper } = await abrir(`${PREFIXO}/clientes/7`, { drawerRota: true })
    await vi.waitFor(() => expect(drawers()).toHaveLength(1))
    await assentar()

    expect(api.listar).toHaveBeenCalledTimes(1)
    expect(api.obter).toHaveBeenCalledWith(7)
    expect(wrapper.findAll('table.v8-tabela tbody tr').length).toBeGreaterThan(0)
    const [drawer] = drawers()
    expect(drawer.classList.contains('v8-drawer-right')).toBe(true)
    expect(drawer.querySelector('.v8-overlay-titulo').textContent.trim()).toBe('Glória Exemplo')
    expect(drawer.textContent).toContain('gloria.exemplo@exemplo.invalid')
    expect(overlaysAbertos().map(e => e.source)).toEqual(['rota'])
    wrapper.unmount()
  })

  it('V8-DEMO-021: abrir a URL do pedido empilha o segundo drawer sobre o do cliente', async () => {
    const { wrapper } = await abrir(`${PREFIXO}/clientes/7/pedidos/702`, { drawerRota: true })
    await vi.waitFor(() => expect(drawers()).toHaveLength(2))
    await assentar()

    const [cliente, pedido] = drawers()
    expect(cliente.querySelector('.v8-overlay-titulo').textContent.trim()).toBe('Glória Exemplo')
    expect(pedido.querySelector('.v8-overlay-titulo').textContent.trim()).toBe('Pedido 702')
    expect(pedido.textContent).toContain('Caixa de canetas')
    expect(pedido.textContent).toContain('138,55')
    expect(pedido.hasAttribute('data-overlay-topo')).toBe(true)
    expect(cliente.hasAttribute('data-overlay-topo')).toBe(false)
    expect(overlaysAbertos().map(e => [e.kind, e.source])).toEqual([['drawer', 'rota'], ['drawer', 'rota']])
    wrapper.unmount()
  })

  it('V8-DEMO-021: fechar o drawer do pedido volta à rota do cliente, e fechar este volta à lista', async () => {
    const { wrapper, router } = await abrir(`${PREFIXO}/clientes/7/pedidos/702`, { drawerRota: true })
    await vi.waitFor(() => expect(drawers()).toHaveLength(2))

    drawers()[1].querySelector('[data-overlay-fechar]').click()
    await vi.waitFor(() => expect(router.currentRoute.value.name).toBe('demo_spa_cliente'))
    expect(router.currentRoute.value.path).toBe(`${PREFIXO}/clientes/7`)

    await vi.waitFor(() => expect(drawers()).toHaveLength(1))
    drawers()[0].querySelector('[data-overlay-fechar]').click()
    await vi.waitFor(() => expect(router.currentRoute.value.name).toBe('demo_spa_clientes'))
    wrapper.unmount()
  })

  it('V8-DEMO-021: pedido que o cliente não tem mostra a mensagem no drawer', async () => {
    const { wrapper } = await abrir(`${PREFIXO}/clientes/7/pedidos/999`, { drawerRota: true })
    await vi.waitFor(() => expect(drawers()).toHaveLength(2))
    await assentar()
    expect(drawers()[1].querySelector('[role="alert"]').textContent).toContain('não tem o pedido 999')
    wrapper.unmount()
  })

  it('V8-DEMO-023: "Novo cliente" abre o modal wizard de três passos, que envia à API ao concluir', async () => {
    const { wrapper } = await abrir(`${PREFIXO}/clientes`)
    await botao(wrapper, 'Novo cliente').trigger('click')

    const abertos = overlaysAbertos()
    expect(abertos).toHaveLength(1)
    expect(abertos[0].kind).toBe('modal')
    expect(abertos[0].type).toBe('wizard')
    expect(abertos[0].titulo).toBe('Novo cliente')
    const props = abertos[0].conteudo.props
    expect(props.passos).toHaveLength(3)
    expect(props.dadosIniciais).toEqual({ nome: '', email: '', cidade: '', situacao: 'ativo', motivo: '' })

    const dados = { nome: 'Novo Modelo', email: 'novo.modelo@exemplo.invalid', cidade: 'Jataí', situacao: 'ativo', motivo: '' }
    const criado = { id: 43, ...dados }
    api.criar.mockResolvedValue(criado)
    await expect(props.concluir(dados)).resolves.toEqual(criado)
    expect(api.criar).toHaveBeenCalledWith(dados)

    // O wizard fecha com a resposta da API, e é a lista que dispara o toast.
    fecharOverlay(abertos[0].id, criado)
    await assentar()
    expect(toasts()).toHaveLength(1)
    expect(toasts()[0].nivel).toBe('success')
    expect(toasts()[0].texto).toContain('Novo Modelo')
    wrapper.unmount()
  })

  it('V8-DEMO-023: wizard dispensado não dispara toast', async () => {
    const { wrapper } = await abrir(`${PREFIXO}/clientes`)
    await botao(wrapper, 'Novo cliente').trigger('click')
    fecharOverlay(overlaysAbertos()[0].id)
    await assentar()
    expect(api.criar).not.toHaveBeenCalled()
    expect(toasts()).toEqual([])
    wrapper.unmount()
  })

  it('V8-DEMO-025: a resposta 403 vira um toast de erro com a mensagem de sem_permissao', async () => {
    api.negado.mockRejectedValue(new HttpError({ status: 403, codigo: 'sem_permissao' }))
    const { wrapper } = await abrir(`${PREFIXO}/clientes`)
    await botao(wrapper, 'Testar acesso negado').trigger('click')
    await assentar()

    expect(api.negado).toHaveBeenCalledTimes(1)
    expect(toasts()).toEqual([
      { nivel: 'error', texto: 'Você não tem permissão para executar esta ação.' }
    ])
    // A tela continua como estava: nenhum overlay, a lista no lugar e o botão de volta.
    expect(overlaysAbertos()).toEqual([])
    expect(wrapper.findAll('table.v8-tabela tbody tr')).toHaveLength(2)
    expect(botao(wrapper, 'Testar acesso negado').element.disabled).toBe(false)
    wrapper.unmount()
  })

  it('V8-DEMO-025: falha que não é a recusa do servidor vira um aviso, e não o toast de erro', async () => {
    api.negado.mockRejectedValue(new HttpError({ status: 0, codigo: 'rede' }))
    const { wrapper } = await abrir(`${PREFIXO}/clientes`)
    await botao(wrapper, 'Testar acesso negado').trigger('click')
    await assentar()
    expect(toasts()).toHaveLength(1)
    expect(toasts()[0].nivel).toBe('warning')
    expect(toasts()[0].texto).toContain('Não foi possível comunicar com o servidor.')
    wrapper.unmount()
  })

  it('V8-DEMO-025: o botão fica desabilitado enquanto a requisição não responde', async () => {
    let rejeitar
    api.negado.mockReturnValue(new Promise((_resolver, recusar) => {
      rejeitar = recusar
    }))
    const { wrapper } = await abrir(`${PREFIXO}/clientes`)
    await botao(wrapper, 'Testar acesso negado').trigger('click')
    expect(botao(wrapper, 'Testar acesso negado').element.disabled).toBe(true)
    rejeitar(new HttpError({ status: 403, codigo: 'sem_permissao', mensagem: 'Só para quem pode.' }))
    await assentar()
    expect(toasts()).toEqual([{ nivel: 'error', texto: 'Só para quem pode.' }])
    wrapper.unmount()
  })
})
