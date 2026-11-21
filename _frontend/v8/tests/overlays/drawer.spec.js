import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, h, ref } from 'vue'
import pinia from '~@/core/pinia'
import Drawer from '~@/overlays/Drawer.vue'
import http from '~@/http/client'
import { assentar, conteudoDeTeste, dialogos, montarHost, novoStore } from './apoio'

let store
let host

function telaLarga(larga) {
  const ouvintes = new Set()
  const consulta = {
    matches: larga,
    media: '(min-width: 64rem)',
    addEventListener: (_tipo, fn) => ouvintes.add(fn),
    removeEventListener: (_tipo, fn) => ouvintes.delete(fn)
  }
  vi.spyOn(window, 'matchMedia').mockImplementation(() => consulta)
  return valor => {
    consulta.matches = valor
    ouvintes.forEach(fn => fn({ matches: valor }))
  }
}

function comDocas() {
  document.body.insertAdjacentHTML('beforeend', `
    <div data-v8-doca="left"></div><main id="conteudo"></main><div data-v8-doca="right"></div>`)
}

beforeEach(() => {
  store = novoStore()
  host = montarHost()
})

afterEach(() => {
  host.unmount()
  store.$limpar()
})

describe('drawer', () => {
  it('V8-OVL-030: lado, tamanho e fundo vêm das opções', async () => {
    telaLarga(true)
    store.openDrawer({ componente: conteudoDeTeste() }, { side: 'left', size: 'lg', scrim: false, title: 'Filtros' })
    await assentar()
    const drawer = dialogos()[0]
    expect(drawer.classList.contains('v8-drawer-left')).toBe(true)
    expect(drawer.classList.contains('v8-tamanho-lg')).toBe(true)
    expect(document.querySelector('.v8-scrim').classList.contains('v8-scrim-transparente')).toBe(true)
  })

  it('V8-OVL-030: tamanho pode ser uma medida CSS', async () => {
    store.openDrawer({ componente: conteudoDeTeste() }, { size: '30rem', title: 'X' })
    await assentar()
    expect(dialogos()[0].style.getPropertyValue('--v8-largura')).toBe('30rem')
  })

  it('V8-OVL-031: cabeçalho com título e fechar, corpo e rodapé de ações', async () => {
    const { default: OverlayFooter } = await import('~@/overlays/OverlayFooter.vue')
    const Conteudo = defineComponent({
      render: () => [h('p', { 'data-corpo': '' }, 'corpo'), h(OverlayFooter, null, () => h('button', { 'data-acao': '' }, 'Salvar'))]
    })
    store.openDrawer({ componente: Conteudo }, { title: 'Cliente' })
    await assentar()
    const drawer = dialogos()[0]
    expect(drawer.querySelector('.v8-overlay-cabecalho .v8-overlay-titulo').textContent.trim()).toBe('Cliente')
    expect(drawer.querySelector('.v8-overlay-cabecalho [data-overlay-fechar]')).not.toBeNull()
    expect(drawer.querySelector('.v8-overlay-corpo [data-corpo]')).not.toBeNull()
    expect(drawer.querySelector('.v8-overlay-rodape [data-acao]')).not.toBeNull()
    expect(drawer.querySelector('.v8-overlay-corpo [data-acao]')).toBeNull()
  })

  it('V8-OVL-032: docked e push não são modais nem entram na pilha', async () => {
    telaLarga(true)
    comDocas()
    store.openDrawer({ componente: conteudoDeTeste({}, 'd') }, { mode: 'docked', side: 'left', title: 'Filtros' })
    store.openDrawer({ componente: conteudoDeTeste({}, 'p') }, { mode: 'push', side: 'right', title: 'Ajuda' })
    await assentar()
    expect(store.pilha).toHaveLength(0)
    const docked = dialogos().find(el => el.classList.contains('v8-lateral-docked'))
    const push = dialogos().find(el => el.classList.contains('v8-lateral-push'))
    expect(docked.getAttribute('role')).toBe('complementary')
    expect(docked.hasAttribute('aria-modal')).toBe(false)
    expect(document.getElementById(docked.getAttribute('aria-labelledby')).textContent.trim()).toBe('Filtros')
    // docked faz parte do layout; push fica fora dele e desloca o conteúdo.
    expect(document.querySelector('[data-v8-doca="left"]').contains(docked)).toBe(true)
    expect(document.querySelector('[data-v8-doca="right"]').contains(push)).toBe(false)
    expect(document.documentElement.style.getPropertyValue('--v8-empurra-right')).not.toBe('')
    expect(document.body.style.pointerEvents).not.toBe('none')
    expect(document.getElementById('conteudo').hasAttribute('aria-hidden')).toBe(false)

    store.close(store.entradas[1].id)
    await assentar()
    expect(document.documentElement.style.getPropertyValue('--v8-empurra-right')).toBe('')
  })

  it('V8-OVL-033: troca de modo ao cruzar a largura de corte, sem recriar o conteúdo', async () => {
    const mudar = telaLarga(true)
    comDocas()
    let montagens = 0
    const Conteudo = defineComponent({
      setup() {
        montagens += 1
        const texto = ref('')
        return () => h('input', { 'data-campo': '', value: texto.value, onInput: e => (texto.value = e.target.value) })
      }
    })
    store.openDrawer({ componente: Conteudo }, { mode: 'docked', modeEstreito: 'overlay', side: 'left', title: 'Filtros' })
    await assentar()
    expect(dialogos()[0].getAttribute('role')).toBe('complementary')
    const campo = document.querySelector('[data-campo]')
    campo.value = 'jataí'
    campo.dispatchEvent(new Event('input'))

    mudar(false)
    await assentar()
    expect(dialogos()[0].getAttribute('role')).toBe('dialog')
    expect(store.pilha).toHaveLength(1)
    expect(document.querySelector('[data-campo]')).toBe(campo)
    expect(campo.value).toBe('jataí')
    expect(montagens).toBe(1)

    mudar(true)
    await assentar()
    expect(dialogos()[0].getAttribute('role')).toBe('complementary')
    expect(store.pilha).toHaveLength(0)
    expect(montagens).toBe(1)
  })

  it('V8-OVL-030: o mesmo componente Drawer serve declarado em template', async () => {
    const aberto = ref(true)
    const w = mount(defineComponent({
      render: () => h(Drawer, {
        open: aberto.value,
        'onUpdate:open': v => (aberto.value = v),
        side: 'left',
        title: 'Declarado'
      }, { default: () => h('p', { 'data-dentro': '' }, 'x'), footer: () => h('button', { 'data-rodape': '' }, 'ok') })
    }), { attachTo: document.body, global: { plugins: [pinia] } })
    await assentar()
    const drawer = dialogos()[0]
    expect(drawer.classList.contains('v8-drawer-left')).toBe(true)
    expect(drawer.querySelector('[data-dentro]')).not.toBeNull()
    expect(drawer.querySelector('.v8-overlay-rodape [data-rodape]')).not.toBeNull()
    expect(store.pilha).toHaveLength(1)
    drawer.querySelector('[data-overlay-fechar]').click()
    await assentar()
    expect(aberto.value).toBe(false)
    expect(store.pilha).toHaveLength(0)
    w.unmount()
  })
})

describe('conteúdo do drawer', () => {
  it('V8-OVL-043: elemento da página é movido para o overlay e devolvido ao fechar', async () => {
    document.body.insertAdjacentHTML('beforeend', `
      <section id="origem"><p>antes</p><form id="demo-filtros"><input name="q" value="abc"></form><p>depois</p></section>`)
    const formulario = document.getElementById('demo-filtros')
    store.openDrawer({ el: 'demo-filtros' }, { title: 'Filtros', side: 'left' })
    await assentar()
    const drawer = dialogos()[0]
    expect(drawer.contains(formulario)).toBe(true)
    expect(document.getElementById('origem').contains(formulario)).toBe(false)
    formulario.querySelector('input').value = 'editado'

    store.close(store.topo.id)
    await assentar()
    const origem = document.getElementById('origem')
    expect(origem.contains(formulario)).toBe(true)
    expect(formulario.previousElementSibling.textContent).toBe('antes')
    expect(formulario.nextElementSibling.textContent).toBe('depois')
    expect(formulario.querySelector('input').value).toBe('editado')
  })

  it('V8-OVL-040: fragmento é buscado em /v8/_frag/ como HTML', async () => {
    const get = vi.spyOn(http, 'get').mockResolvedValue('<section><h2 data-overlay-title>Histórico de Ana</h2><p data-frag>ok</p></section>')
    store.openDrawer({ frag: 'demo/cliente/7/historico' }, { title: 'Histórico' })
    await assentar()
    expect(get).toHaveBeenCalledWith('/v8/_frag/demo/cliente/7/historico/', { accept: 'html' })
    expect(dialogos()[0].querySelector('[data-frag]')).not.toBeNull()
  })

  it('V8-OVL-042: o título do fragmento vira o título do overlay', async () => {
    vi.spyOn(http, 'get').mockResolvedValue('<h2 data-overlay-title>Histórico de Ana</h2>')
    store.openDrawer({ frag: 'demo/cliente/7/historico' }, { title: 'Do gatilho' })
    await assentar()
    expect(store.topo.titulo).toBe('Histórico de Ana')
  })

  it('V8-OVL-042: sem título no fragmento, vale o do gatilho', async () => {
    vi.spyOn(http, 'get').mockResolvedValue('<p>sem título</p>')
    store.openDrawer({ frag: 'demo/ajuda' }, { title: 'Do gatilho' })
    await assentar()
    expect(store.topo.titulo).toBe('Do gatilho')
  })

  it('V8-OVL-041: o overlay abre antes de o fragmento chegar e mostra erro com nova tentativa', async () => {
    let rejeitar
    const get = vi.spyOn(http, 'get').mockImplementationOnce(() => new Promise((_ok, falha) => (rejeitar = falha)))
    store.openDrawer({ frag: 'demo/ajuda' }, { title: 'Ajuda' })
    await assentar()
    const drawer = dialogos()[0]
    expect(drawer.querySelector('[role="status"]').textContent).toContain('Carregando')
    rejeitar({ mensagem: 'Sem conexão.' })
    await assentar()
    expect(drawer.querySelector('[role="alert"]').textContent).toContain('Sem conexão.')
    get.mockResolvedValueOnce('<p data-frag>agora foi</p>')
    drawer.querySelector('[role="alert"] button').click()
    await assentar()
    expect(drawer.querySelector('[data-frag]')).not.toBeNull()
  })

  it('V8-OVL-044: ilhas e gatilhos dentro de um fragmento funcionam como na página', async () => {
    const { default: IslandHost } = await import('~@/core/IslandHost.vue')
    const { iniciarGatilhos } = await import('~@/core/triggers')
    const Ilha = defineComponent({ render: () => h('p', { 'data-ilha-viva': '' }, 'viva') })
    const ilhas = mount(IslandHost, {
      props: { registro: { resumo: () => Promise.resolve({ default: Ilha }) } },
      attachTo: document.body
    })
    const parar = iniciarGatilhos()
    document.body.insertAdjacentHTML('beforeend', '<div id="ajuda-pagina"><p>ajuda</p></div>')
    vi.spyOn(http, 'get').mockResolvedValue(`
      <div data-vue-island="resumo"><p data-espera>do servidor</p></div>
      <button id="gatilho-frag" type="button" data-drawer="el:#ajuda-pagina" data-drawer-title="Ajuda">Ajuda</button>`)
    store.openDrawer({ frag: 'demo/cliente/7/historico' }, { title: 'Histórico' })
    await assentar()
    const fragmento = dialogos()[0]
    expect(fragmento.querySelector('[data-ilha-viva]')).not.toBeNull()
    expect(fragmento.querySelector('[data-espera]')).toBeNull()

    document.getElementById('gatilho-frag').click()
    await assentar()
    expect(store.pilha.map(e => e.titulo)).toEqual(['Histórico', 'Ajuda'])
    parar()
    ilhas.unmount()
  })

  it('V8-OVL-103: o HTML do fragmento não executa script', async () => {
    window.__v8Executou = false
    vi.spyOn(http, 'get').mockResolvedValue('<p>ok</p><script>window.__v8Executou = true</script>')
    store.openDrawer({ frag: 'demo/ajuda' }, { title: 'Ajuda' })
    await assentar()
    expect(window.__v8Executou).toBe(false)
    delete window.__v8Executou
  })

  it('V8-OVL-100: caminho de fragmento inválido não gera requisição', async () => {
    const get = vi.spyOn(http, 'get').mockResolvedValue('<p>x</p>')
    store.openDrawer({ frag: '../../admin' }, { title: 'X' })
    await assentar()
    expect(get).not.toHaveBeenCalled()
    expect(dialogos()[0].querySelector('[role="alert"]')).not.toBeNull()
  })
})
