import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { h } from 'vue'
import { RouterView } from 'vue-router'
import { HttpError } from '~@/http/client'
import OverlayHost from '~@/overlays/OverlayHost.vue'
import * as api from '~@/modules/demo/api'
import ClienteForm from '~@/modules/demo/modais/ClienteForm.vue'
import ClienteResumo from '~@/modules/demo/modais/ClienteResumo.vue'
import ClienteDetalhe from '~@/modules/demo/spa/ClienteDetalhe.vue'
import PedidoDetalhe from '~@/modules/demo/spa/PedidoDetalhe.vue'
import {
  PREFIXO,
  assentar,
  clienteDeExemplo,
  comOverlay,
  criarRouterDaZona,
  fecharOverlay,
  limparStores,
  overlayDeMentira,
  overlaysAbertos,
  paginaDeExemplo,
  toasts
} from './apoio'

vi.mock('~@/modules/demo/api')

// O componente sozinho, com um overlay de mentira no lugar do drawer da rota.
async function montar(componente = ClienteDetalhe, props = { id: 7 }) {
  const overlay = overlayDeMentira()
  const router = criarRouterDaZona()
  router.push(`${PREFIXO}/clientes/7`)
  await router.isReady()
  const wrapper = mount(componente, {
    props,
    global: {
      plugins: [router],
      provide: comOverlay(overlay),
      stubs: { DrawerRota: true }
    },
    attachTo: document.body
  })
  await assentar()
  return { wrapper, overlay, router }
}

function botao(wrapper, texto) {
  return wrapper.findAll('button').find(b => b.text() === texto)
}

describe('detalhe do cliente na zona SPA', () => {
  beforeEach(() => {
    api.obter.mockImplementation(async id => clienteDeExemplo({ id }))
  })

  afterEach(limparStores)

  it('V8-DEMO-021: carrega o cliente, mostra os dados e põe o nome no título do drawer', async () => {
    const { wrapper, overlay } = await montar()
    expect(api.obter).toHaveBeenCalledWith(7)
    expect(overlay.setTitle).toHaveBeenLastCalledWith('Glória Exemplo')
    const dados = wrapper.find('dl.v8-lista-dados').text()
    expect(dados).toContain('gloria.exemplo@exemplo.invalid')
    expect(dados).toContain('Jataí')
    expect(dados).toContain('07/09/2021')
    expect(wrapper.findComponent({ name: 'DrawerRota' }).exists()).toBe(true)
    wrapper.unmount()
  })

  it('V8-DEMO-021: cada pedido leva à rota aninhada do pedido', async () => {
    const { wrapper, router } = await montar()
    const links = wrapper.findAll('table.v8-tabela tbody a')
    expect(links.map(a => a.text())).toEqual(['Caderno de anotações', 'Caixa de canetas'])
    expect(links.map(a => a.attributes('href'))).toEqual([
      `${PREFIXO}/clientes/7/pedidos/701`,
      `${PREFIXO}/clientes/7/pedidos/702`
    ])
    await links[1].trigger('click')
    await assentar()
    expect(router.currentRoute.value.name).toBe('demo_spa_pedido')
    expect(router.currentRoute.value.params).toEqual({ id: '7', pedido: '702' })
    wrapper.unmount()
  })

  it('V8-DEMO-021: trocar o id carrega o outro cliente no mesmo drawer', async () => {
    api.obter.mockImplementation(async id => clienteDeExemplo({ id, nome: `Cliente ${id}` }))
    const { wrapper, overlay } = await montar()
    expect(overlay.setTitle).toHaveBeenLastCalledWith('Cliente 7')

    await wrapper.setProps({ id: 8 })
    expect(wrapper.find('[role="status"]').exists()).toBe(true)
    expect(wrapper.find('dl').exists()).toBe(false)
    await assentar()
    expect(api.obter).toHaveBeenLastCalledWith(8)
    expect(overlay.setTitle).toHaveBeenLastCalledWith('Cliente 8')
    expect(wrapper.find('table.v8-tabela tbody a').attributes('href')).toBe(`${PREFIXO}/clientes/8/pedidos/701`)
    wrapper.unmount()
  })

  it('V8-DEMO-021: falha ao carregar mostra o erro, sem as ações, e permite tentar de novo', async () => {
    api.obter.mockRejectedValueOnce(new HttpError({ status: 500, codigo: 'servidor' }))
    const { wrapper } = await montar()
    expect(wrapper.find('[role="alert"]').text()).toContain('O servidor encontrou um erro.')
    expect(botao(wrapper, 'Editar')).toBeUndefined()

    await botao(wrapper, 'Tentar de novo').trigger('click')
    await assentar()
    expect(wrapper.find('dl.v8-lista-dados').exists()).toBe(true)
    expect(botao(wrapper, 'Editar')).toBeDefined()
    wrapper.unmount()
  })

  it('V8-DEMO-022: "Editar" abre o modal form com os dados do cliente', async () => {
    const { wrapper } = await montar()
    await botao(wrapper, 'Editar').trigger('click')

    const abertos = overlaysAbertos()
    expect(abertos).toHaveLength(1)
    expect(abertos[0].kind).toBe('modal')
    expect(abertos[0].type).toBe('form')
    expect(abertos[0].titulo).toBe('Editar cliente')
    expect(abertos[0].conteudo.props.cliente).toEqual(clienteDeExemplo())
    expect((await abertos[0].conteudo.componente()).default).toBe(ClienteForm)
    wrapper.unmount()
  })

  it('V8-DEMO-022: ao salvar, mostra os dados novos e dispara o toast de sucesso', async () => {
    const { wrapper, overlay } = await montar()
    await botao(wrapper, 'Editar').trigger('click')
    // A resposta da API não precisa trazer os pedidos: os da tela são mantidos.
    const { pedidos, ...salvo } = clienteDeExemplo({ nome: 'Glória Modelo', cidade: 'Mineiros' })
    fecharOverlay(overlaysAbertos()[0].id, salvo)
    await assentar()

    expect(toasts()).toEqual([
      { nivel: 'success', texto: 'Cliente salvo. Demonstração: nada foi gravado.' }
    ])
    expect(wrapper.find('dl.v8-lista-dados').text()).toContain('Mineiros')
    expect(overlay.setTitle).toHaveBeenLastCalledWith('Glória Modelo')
    expect(wrapper.findAll('table.v8-tabela tbody a')).toHaveLength(pedidos.length)
    // Salvar não busca o cliente de novo.
    expect(api.obter).toHaveBeenCalledTimes(1)
    wrapper.unmount()
  })

  it('V8-DEMO-022: modal dispensado não muda os dados nem dispara toast', async () => {
    const { wrapper } = await montar()
    await botao(wrapper, 'Editar').trigger('click')
    fecharOverlay(overlaysAbertos()[0].id)
    await assentar()
    expect(toasts()).toEqual([])
    expect(wrapper.find('dl.v8-lista-dados').text()).toContain('Jataí')
    wrapper.unmount()
  })

  it('V8-DEMO-024: "Ampliar" abre o modal fullscreen com o resumo do cliente', async () => {
    const { wrapper } = await montar()
    await botao(wrapper, 'Ampliar').trigger('click')

    const abertos = overlaysAbertos()
    expect(abertos).toHaveLength(1)
    expect(abertos[0].kind).toBe('modal')
    expect(abertos[0].type).toBe('fullscreen')
    expect(abertos[0].titulo).toBe('Resumo do cliente')
    expect(abertos[0].conteudo.props).toEqual({ id: 7 })
    expect((await abertos[0].conteudo.componente()).default).toBe(ClienteResumo)
    wrapper.unmount()
  })
})

describe('pedido do cliente na zona SPA', () => {
  beforeEach(() => {
    api.obter.mockResolvedValue(clienteDeExemplo())
  })

  afterEach(limparStores)

  it('V8-DEMO-021: mostra o pedido pedido na rota e põe o número no título do drawer', async () => {
    const { wrapper, overlay } = await montar(PedidoDetalhe, { id: 7, pedido: 702 })
    expect(api.obter).toHaveBeenCalledWith(7)
    const dados = wrapper.find('dl.v8-lista-dados').text()
    expect(dados).toContain('702')
    expect(dados).toContain('Caixa de canetas')
    expect(dados).toContain('06/11/2021')
    expect(dados).toContain('138,55')
    expect(dados).toContain('Glória Exemplo')
    expect(dados).not.toContain('Caderno de anotações')
    expect(overlay.setTitle).toHaveBeenCalledWith('Pedido 702')
    wrapper.unmount()
  })

  it('V8-DEMO-021: pedido de outro cliente não é mostrado', async () => {
    const { wrapper, overlay } = await montar(PedidoDetalhe, { id: 7, pedido: 801 })
    expect(wrapper.find('dl').exists()).toBe(false)
    expect(wrapper.find('[role="alert"]').text()).toContain('não tem o pedido 801')
    expect(overlay.setTitle).not.toHaveBeenCalled()
    wrapper.unmount()
  })

  it('V8-DEMO-021: cliente inexistente mostra a mensagem da API', async () => {
    api.obter.mockRejectedValue(new HttpError({ status: 404, codigo: 'nao_encontrado' }))
    const { wrapper } = await montar(PedidoDetalhe, { id: 999, pedido: 1 })
    expect(wrapper.find('[role="alert"]').text()).toContain('não foi encontrado')
    expect(botao(wrapper, 'Tentar de novo')).toBeUndefined()
    wrapper.unmount()
  })
})

// A zona inteira, com o router, os drawers de rota e a pilha de overlays de verdade.
describe('edição do cliente de ponta a ponta', () => {
  beforeEach(() => {
    api.listar.mockResolvedValue(paginaDeExemplo())
    api.obter.mockResolvedValue(clienteDeExemplo())
  })

  afterEach(limparStores)

  async function abrirDetalhe() {
    const router = criarRouterDaZona()
    router.push(`${PREFIXO}/clientes/7`)
    await router.isReady()
    const wrapper = mount({ render: () => [h(RouterView), h(OverlayHost)] }, {
      global: { plugins: [router] },
      attachTo: document.body
    })
    await vi.waitFor(() => expect(botaoEm(drawer(), 'Editar')).toBeTruthy())
    return { wrapper, router }
  }

  function drawer() {
    return document.querySelector('[data-overlay-kind="drawer"]')
  }

  function modal(seletor = '[role="dialog"]') {
    return document.querySelector(`[data-overlay-kind="modal"]${seletor}`)
  }

  function botaoEm(raiz, texto) {
    return [...(raiz?.querySelectorAll('button, a') || [])].find(b => b.textContent.trim() === texto)
  }

  function campo(raiz, rotulo) {
    const label = [...raiz.querySelectorAll('label')].find(l => l.textContent.trim() === rotulo)
    return raiz.querySelector(`[id="${label.getAttribute('for')}"]`)
  }

  async function digitar(entrada, valor) {
    entrada.value = valor
    entrada.dispatchEvent(new Event('input', { bubbles: true }))
    await assentar()
  }

  async function abrirEdicao() {
    botaoEm(drawer(), 'Editar').click()
    await vi.waitFor(() => expect(modal()?.querySelector('form')).toBeTruthy())
    return modal()
  }

  it('V8-DEMO-022: fechar com alteração pendente pede confirmação, e recusar mantém o modal', async () => {
    const { wrapper } = await abrirDetalhe()
    const formulario = await abrirEdicao()
    expect(formulario.querySelector('.v8-overlay-titulo').textContent.trim()).toBe('Editar cliente')
    await digitar(campo(formulario, 'Cidade'), 'Mineiros')

    botaoEm(formulario, 'Cancelar').click()
    await vi.waitFor(() => expect(modal('[role="alertdialog"]')).toBeTruthy())
    const confirmacao = modal('[role="alertdialog"]')
    expect(confirmacao.textContent).toContain('Descartar alterações?')

    confirmacao.querySelector('[data-confirm-botao=cancelar]').click()
    await vi.waitFor(() => expect(modal('[role="alertdialog"]')).toBeNull())
    expect(modal()).toBe(formulario)
    expect(campo(formulario, 'Cidade').value).toBe('Mineiros')
    expect(api.salvar).not.toHaveBeenCalled()
    expect(toasts()).toEqual([])
    wrapper.unmount()
  })

  it('V8-DEMO-022: confirmar o descarte fecha o modal sem salvar', async () => {
    const { wrapper } = await abrirDetalhe()
    const formulario = await abrirEdicao()
    await digitar(campo(formulario, 'Cidade'), 'Mineiros')

    formulario.querySelector('[data-overlay-fechar]').click()
    await vi.waitFor(() => expect(modal('[role="alertdialog"]')).toBeTruthy())
    modal('[role="alertdialog"]').querySelector('[data-confirm-botao=ok]').click()
    await vi.waitFor(() => expect(overlaysAbertos().filter(e => e.kind === 'modal')).toEqual([]))
    await assentar()

    expect(api.salvar).not.toHaveBeenCalled()
    expect(toasts()).toEqual([])
    expect(drawer().textContent).toContain('Jataí')
    wrapper.unmount()
  })

  it('V8-DEMO-022: sem alteração, "Cancelar" fecha direto', async () => {
    const { wrapper } = await abrirDetalhe()
    const formulario = await abrirEdicao()
    botaoEm(formulario, 'Cancelar').click()
    await vi.waitFor(() => expect(overlaysAbertos().filter(e => e.kind === 'modal')).toEqual([]))
    expect(modal('[role="alertdialog"]')).toBeNull()
    wrapper.unmount()
  })

  it('V8-DEMO-022: erro da API fica no modal, e salvar com sucesso o fecha, atualiza o drawer e dispara o toast', async () => {
    api.salvar.mockRejectedValueOnce(new HttpError({
      status: 400,
      codigo: 'validacao',
      campos: { email: ['Este e-mail já é usado por outro cliente.'] },
      gerais: ['Cliente inativo precisa de um motivo preenchido.']
    }))
    const { wrapper } = await abrirDetalhe()
    const formulario = await abrirEdicao()
    await digitar(campo(formulario, 'E-mail'), 'ana.exemplo@exemplo.invalid')
    await digitar(campo(formulario, 'Cidade'), 'Mineiros')

    botaoEm(formulario, 'Salvar').click()
    await vi.waitFor(() => expect(formulario.querySelector('.v8-erro-campo')).toBeTruthy())
    expect(formulario.querySelector('.v8-erro-campo').textContent.trim()).toBe('Este e-mail já é usado por outro cliente.')
    expect(formulario.querySelector('form [role="alert"]').textContent).toContain('Cliente inativo precisa de um motivo preenchido.')
    expect(modal()).toBe(formulario)
    expect(toasts()).toEqual([])

    const { pedidos, ...corpo } = clienteDeExemplo({ email: 'gloria.modelo@exemplo.invalid', cidade: 'Mineiros' })
    expect(pedidos).toHaveLength(2)
    api.salvar.mockResolvedValueOnce(corpo)
    await digitar(campo(formulario, 'E-mail'), 'gloria.modelo@exemplo.invalid')
    botaoEm(formulario, 'Salvar').click()
    await vi.waitFor(() => expect(toasts()).toHaveLength(1))

    expect(api.salvar).toHaveBeenLastCalledWith(7, {
      nome: 'Glória Exemplo',
      email: 'gloria.modelo@exemplo.invalid',
      cidade: 'Mineiros',
      situacao: 'ativo',
      motivo: ''
    })
    expect(toasts()[0]).toEqual({ nivel: 'success', texto: 'Cliente salvo. Demonstração: nada foi gravado.' })
    expect(overlaysAbertos().map(e => e.kind)).toEqual(['drawer'])
    expect(drawer().textContent).toContain('gloria.modelo@exemplo.invalid')
    expect(drawer().textContent).toContain('Mineiros')
    wrapper.unmount()
  })

  it('V8-DEMO-024: "Ampliar" mostra o resumo num modal de tela cheia sobre o drawer', async () => {
    const { wrapper } = await abrirDetalhe()
    botaoEm(drawer(), 'Ampliar').click()
    await vi.waitFor(() => expect(modal()?.querySelector('dl.v8-lista-dados')).toBeTruthy())

    const resumo = modal()
    expect(resumo.classList.contains('v8-modal-fullscreen')).toBe(true)
    expect(resumo.querySelector('.v8-overlay-titulo').textContent.trim()).toBe('Resumo do cliente')
    expect(resumo.textContent).toContain('Glória Exemplo')
    expect(resumo.textContent).toContain('2 pedidos')
    expect(resumo.hasAttribute('data-overlay-topo')).toBe(true)

    botaoEm(resumo, 'Fechar').click()
    await vi.waitFor(() => expect(overlaysAbertos().map(e => e.kind)).toEqual(['drawer']))
    wrapper.unmount()
  })
})
