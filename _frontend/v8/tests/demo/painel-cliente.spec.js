import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { modais } from '~@/core/modais'
import { paineis } from '~@/core/paineis'
import { HttpError } from '~@/http/client'
import { interpretarAlvo, resolverAlvo, urlDoFragmento } from '~@/overlays/alvo'
import * as api from '~@/modules/demo/api'
import ClienteResumo from '~@/modules/demo/modais/ClienteResumo.vue'
import PainelCliente from '~@/modules/demo/paineis/PainelCliente.vue'
import { assentar, clienteDeExemplo, comOverlay, limparStores, overlayDeMentira, toasts } from './apoio'

vi.mock('~@/modules/demo/api')

function montar(componente, overlay = overlayDeMentira()) {
  const wrapper = mount(componente, {
    props: { id: 7 },
    global: { provide: comOverlay(overlay) },
    attachTo: document.body
  })
  return { wrapper, overlay }
}

function botao(wrapper, texto) {
  return wrapper.findAll('button').find(b => b.text() === texto)
}

function link(wrapper, texto) {
  return wrapper.findAll('a').find(a => a.text() === texto)
}

function definirClipboard(valor) {
  Object.defineProperty(navigator, 'clipboard', { value: valor, configurable: true })
}

describe('painel do cliente', () => {
  beforeEach(() => {
    api.obter.mockResolvedValue(clienteDeExemplo())
  })

  afterEach(() => {
    limparStores()
    delete navigator.clipboard
  })

  it('V8-DEMO-013: o registro de painéis abre este componente com o id da URL', async () => {
    const modulo = await paineis.cliente.componente()
    expect(modulo.default).toBe(PainelCliente)
    expect(paineis.cliente.props('7')).toEqual({ id: 7 })
    expect(paineis.cliente.opcoes.side).toBe('right')
  })

  it('V8-DEMO-013: carrega o cliente da API, mostra os dados e põe o nome no título do drawer', async () => {
    const { wrapper, overlay } = montar(PainelCliente)
    expect(wrapper.find('[role="status"]').text()).toBe('Carregando…')
    expect(api.obter).toHaveBeenCalledWith(7)
    await assentar()

    expect(wrapper.find('[role="status"]').exists()).toBe(false)
    expect(overlay.setTitle).toHaveBeenCalledWith('Glória Exemplo')
    const dados = wrapper.find('dl.v8-lista-dados').text()
    expect(dados).toContain('gloria.exemplo@exemplo.invalid')
    expect(dados).toContain('Jataí')
    expect(dados).toContain('Ativo')
    expect(dados).toContain('07/09/2021')
    const pedidos = wrapper.findAll('table.v8-tabela tbody tr')
    expect(pedidos).toHaveLength(2)
    expect(pedidos[0].text()).toContain('Caderno de anotações')
    expect(pedidos[0].text()).toContain('07/10/2021')
    expect(pedidos[0].text()).toContain('19,90')
    wrapper.unmount()
  })

  it('V8-DEMO-013: falha ao carregar mostra o erro e permite tentar de novo', async () => {
    api.obter.mockRejectedValueOnce(new HttpError({ status: 500, codigo: 'servidor' }))
    const { wrapper, overlay } = montar(PainelCliente)
    await assentar()

    const alerta = wrapper.find('[role="alert"]')
    expect(alerta.text()).toContain('O servidor encontrou um erro.')
    expect(wrapper.find('dl').exists()).toBe(false)
    expect(overlay.setTitle).not.toHaveBeenCalled()

    await botao(wrapper, 'Tentar de novo').trigger('click')
    await assentar()
    expect(api.obter).toHaveBeenCalledTimes(2)
    expect(wrapper.find('[role="alert"]').exists()).toBe(false)
    expect(wrapper.find('dl.v8-lista-dados').exists()).toBe(true)
    wrapper.unmount()
  })

  it('V8-DEMO-013: cliente inexistente mostra a mensagem, sem oferecer nova tentativa', async () => {
    api.obter.mockRejectedValue(new HttpError({ status: 404, codigo: 'nao_encontrado' }))
    const { wrapper } = montar(PainelCliente)
    await assentar()
    expect(wrapper.find('[role="alert"]').text()).toContain('não foi encontrado')
    expect(botao(wrapper, 'Tentar de novo')).toBeUndefined()
    wrapper.unmount()
  })

  it('V8-DEMO-014: "Histórico" é o gatilho do segundo drawer, com o fragmento do cliente', async () => {
    const { wrapper } = montar(PainelCliente)
    await assentar()
    const historico = link(wrapper, 'Histórico')
    expect(historico.attributes('data-drawer')).toBe('frag:demo/cliente/7/historico')
    expect(historico.attributes('data-drawer-side')).toBe('right')
    // Sem JavaScript o link leva ao mesmo fragmento que o drawer busca.
    const alvo = interpretarAlvo(historico.attributes('data-drawer'))
    expect(alvo).toEqual({ tipo: 'frag', caminho: 'demo/cliente/7/historico' })
    expect(historico.attributes('href')).toBe(urlDoFragmento(alvo.caminho))
    wrapper.unmount()
  })

  it('V8-DEMO-024: "Ampliar" é o gatilho do modal de tela cheia com o resumo', async () => {
    const { wrapper } = montar(PainelCliente)
    await assentar()
    const ampliar = link(wrapper, 'Ampliar')
    expect(ampliar.attributes('href')).toBe('/v8/demo/clientes/7/')
    expect(ampliar.attributes('data-modal')).toBe('demo-resumo:7')

    const resolvido = resolverAlvo(ampliar.attributes('data-modal'), modais)
    expect(resolvido.opcoes.type).toBe('fullscreen')
    expect(resolvido.conteudo.props).toEqual({ id: 7 })
    expect((await resolvido.conteudo.componente()).default).toBe(ClienteResumo)
    wrapper.unmount()
  })

  it('V8-DEMO-013: "Copiar e-mail" copia o endereço e avisa com um toast do Vue', async () => {
    const writeText = vi.fn().mockResolvedValue()
    definirClipboard({ writeText })
    const { wrapper } = montar(PainelCliente)
    await assentar()
    await botao(wrapper, 'Copiar e-mail').trigger('click')
    await assentar()
    expect(writeText).toHaveBeenCalledWith('gloria.exemplo@exemplo.invalid')
    expect(toasts()).toEqual([{ nivel: 'success', texto: 'E-mail copiado.' }])
    wrapper.unmount()
  })

  it('V8-DEMO-013: sem área de transferência, o toast informa o endereço', async () => {
    definirClipboard(undefined)
    const { wrapper } = montar(PainelCliente)
    await assentar()
    await botao(wrapper, 'Copiar e-mail').trigger('click')
    await assentar()
    expect(toasts()).toHaveLength(1)
    expect(toasts()[0].nivel).toBe('info')
    expect(toasts()[0].texto).toContain('gloria.exemplo@exemplo.invalid')
    wrapper.unmount()
  })

  it('V8-DEMO-013: cópia recusada pelo navegador também vira o toast com o endereço', async () => {
    definirClipboard({ writeText: vi.fn().mockRejectedValue(new Error('recusada')) })
    const { wrapper } = montar(PainelCliente)
    await assentar()
    await botao(wrapper, 'Copiar e-mail').trigger('click')
    await assentar()
    expect(toasts().map(t => t.nivel)).toEqual(['info'])
    wrapper.unmount()
  })
})

describe('resumo do cliente', () => {
  beforeEach(() => {
    api.obter.mockResolvedValue(clienteDeExemplo({ situacao: 'inativo', motivo: 'Cadastro duplicado' }))
  })

  afterEach(limparStores)

  it('V8-DEMO-024: carrega o cliente e mostra os dados, os pedidos e o total', async () => {
    const { wrapper } = montar(ClienteResumo)
    expect(wrapper.find('[role="status"]').exists()).toBe(true)
    await assentar()

    expect(api.obter).toHaveBeenCalledWith(7)
    expect(wrapper.text()).toContain('Glória Exemplo')
    const dados = wrapper.find('dl.v8-lista-dados').text()
    expect(dados).toContain('Inativo')
    expect(dados).toContain('Cadastro duplicado')
    expect(wrapper.findAll('table.v8-tabela tbody tr')).toHaveLength(2)
    expect(wrapper.text()).toContain('2 pedidos')
    expect(wrapper.text()).toContain('158,45')
    wrapper.unmount()
  })

  it('V8-DEMO-024: "Fechar" fecha o modal', async () => {
    const { wrapper, overlay } = montar(ClienteResumo)
    await assentar()
    await botao(wrapper, 'Fechar').trigger('click')
    expect(overlay.close).toHaveBeenCalledTimes(1)
    wrapper.unmount()
  })

  it('V8-DEMO-024: falha ao carregar mostra o erro dentro do modal', async () => {
    api.obter.mockRejectedValue(new HttpError({ status: 0, codigo: 'rede' }))
    const { wrapper } = montar(ClienteResumo)
    await assentar()
    expect(wrapper.find('[role="alert"]').text()).toContain('Não foi possível comunicar com o servidor.')
    expect(botao(wrapper, 'Tentar de novo')).toBeDefined()
    expect(botao(wrapper, 'Fechar')).toBeDefined()
    wrapper.unmount()
  })
})
