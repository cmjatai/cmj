import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory } from 'vue-router'
import { criarRouter } from '~@/core/router'
import { iniciarGatilhos } from '~@/core/triggers'
import { assentar, conteudoDeTeste, dialogos, montarHost, novoStore, tecla } from './apoio'

vi.mock('~@/core/navegacao', () => {
  const api = { ir: vi.fn(), recarregar: vi.fn(), abrirNovaAba: vi.fn(), caminhoAtual: () => '/v8/demo/clientes/' }
  return { ...api, default: api }
})

let store
let host
let router
let controles
let pararGatilhos

const PAGINA = '/v8/demo/clientes/'

async function preparar(inicial = PAGINA) {
  controles = {}
  const registroDePaineis = {
    cliente: {
      componente: conteudoDeTeste(controles, 'cliente'),
      props: arg => ({ texto: `cliente ${arg}` }),
      opcoes: { side: 'right', title: 'Cliente' }
    },
    pedido: { componente: conteudoDeTeste(controles, 'pedido'), opcoes: { title: 'Pedido' } }
  }
  const historico = createMemoryHistory()
  router = await criarRouter({ zona: null, prefixoZona: null }, { historico, registroDePaineis })
  await router.push(inicial)
  await router.isReady()
  await assentar()
}

function painel() {
  const valor = router.currentRoute.value.query.painel
  return valor === undefined ? [] : [].concat(valor)
}

beforeEach(() => {
  store = novoStore()
  host = montarHost()
})

afterEach(() => {
  pararGatilhos?.()
  pararGatilhos = null
  host.unmount()
  store.$limpar()
})

describe('drawer na query string', () => {
  it('V8-OVL-050: abrir um painel põe o valor em ?painel=, na ordem da pilha', async () => {
    await preparar()
    const { useDrawer } = await import('~@/overlays/useDrawer')
    const { openPanel } = useDrawer()
    await openPanel('cliente:42')
    await assentar()
    expect(painel()).toEqual(['cliente:42'])
    expect(router.currentRoute.value.path).toBe(PAGINA)
    expect(document.querySelector('[data-teste-botao="cliente"]').textContent).toBe('cliente 42')

    await openPanel('pedido:7')
    await assentar()
    expect(painel()).toEqual(['cliente:42', 'pedido:7'])
    expect(store.pilha.map(e => e.chave)).toEqual(['cliente:42', 'pedido:7'])
  })

  it('V8-OVL-051: o botão voltar fecha o drawer e o avançar reabre', async () => {
    await preparar()
    const { abrirPainel } = await import('~@/overlays/urlSync')
    await abrirPainel('cliente:42')
    await assentar()
    expect(store.pilha).toHaveLength(1)

    router.back()
    await assentar()
    expect(painel()).toEqual([])
    expect(store.pilha).toHaveLength(0)

    router.forward()
    await assentar()
    expect(painel()).toEqual(['cliente:42'])
    expect(store.pilha.map(e => e.chave)).toEqual(['cliente:42'])
  })

  it('V8-OVL-052: abrir a página com painel na URL abre os drawers na mesma ordem', async () => {
    await preparar(`${PAGINA}?q=ana&painel=cliente:42&painel=pedido:7`)
    expect(store.pilha.map(e => e.chave)).toEqual(['cliente:42', 'pedido:7'])
    expect(dialogos()).toHaveLength(2)
    expect(router.currentRoute.value.query.q).toBe('ana')
  })

  it('V8-OVL-100: valor de painel desconhecido ou em forma de URL é ignorado', async () => {
    await preparar(`${PAGINA}?painel=https://exemplo.invalid/x&painel=segredo:1&painel=frag:../../admin&painel=cliente:1`)
    expect(store.pilha.map(e => e.chave)).toEqual(['cliente:1'])
  })

  it('V8-OVL-051: fechar pelo ESC tira o valor da URL', async () => {
    await preparar()
    const { abrirPainel } = await import('~@/overlays/urlSync')
    await abrirPainel('cliente:42')
    await abrirPainel('pedido:7')
    await assentar()
    tecla('Escape')
    await assentar()
    expect(painel()).toEqual(['cliente:42'])
    expect(store.pilha.map(e => e.chave)).toEqual(['cliente:42'])
  })

  it('V8-OVL-052: em link aberto direto, fechar troca a URL sem sair da página', async () => {
    await preparar(`${PAGINA}?q=ana&painel=cliente:42`)
    dialogos()[0].querySelector('[data-overlay-fechar]').click()
    await assentar()
    expect(router.currentRoute.value.path).toBe(PAGINA)
    expect(router.currentRoute.value.query).toEqual({ q: 'ana' })
    expect(store.pilha).toHaveLength(0)
  })

  it('V8-OVL-012: fechar o painel de baixo fecha também o de cima e limpa a URL', async () => {
    await preparar()
    const { abrirPainel } = await import('~@/overlays/urlSync')
    await abrirPainel('cliente:42')
    await abrirPainel('pedido:7')
    await assentar()
    store.close(store.pilha[0].id)
    await assentar()
    expect(painel()).toEqual([])
    expect(store.pilha).toHaveLength(0)
  })

  it('V8-OVL-024: com alteração, o botão voltar pede confirmação e, recusada, a URL não muda', async () => {
    await preparar()
    const { abrirPainel } = await import('~@/overlays/urlSync')
    await abrirPainel('cliente:42')
    await assentar()
    controles.cliente.setDirty(true)

    router.back()
    await assentar()
    expect(store.topo.type).toBe('confirm')
    document.querySelector('[data-confirm-botao=cancelar]').click()
    await assentar()
    expect(painel()).toEqual(['cliente:42'])
    expect(store.pilha.map(e => e.chave)).toEqual(['cliente:42'])

    router.back()
    await assentar()
    document.querySelector('[data-confirm-botao=ok]').click()
    await assentar()
    expect(painel()).toEqual([])
    expect(store.pilha).toHaveLength(0)
  })
})

describe('gatilhos em HTML', () => {
  function clicar(el, opcoes = {}) {
    const evento = new MouseEvent('click', { bubbles: true, cancelable: true, button: 0, ...opcoes })
    el.dispatchEvent(evento)
    return evento
  }

  async function comPagina(html) {
    await preparar()
    document.body.insertAdjacentHTML('beforeend', html)
    pararGatilhos = iniciarGatilhos({
      modais: {
        resumo: { componente: conteudoDeTeste(controles, 'resumo'), props: arg => ({ texto: `resumo ${arg}` }), opcoes: { type: 'fullscreen' } }
      }
    })
  }

  it('V8-OVL-081: data-drawer com nome abre o painel e não segue o link', async () => {
    await comPagina('<a id="g" href="/v8/demo/clientes/42/" data-drawer="cliente:42" data-drawer-side="left" data-drawer-size="lg">Ana</a>')
    const evento = clicar(document.getElementById('g'))
    await assentar()
    expect(evento.defaultPrevented).toBe(true)
    expect(painel()).toEqual(['cliente:42'])
    const drawer = dialogos()[0]
    expect(drawer.classList.contains('v8-drawer-left')).toBe(true)
    expect(drawer.classList.contains('v8-tamanho-lg')).toBe(true)
  })

  it('V8-OVL-080: gatilho inserido depois funciona sem novo registro', async () => {
    await comPagina('<div id="alvo"></div>')
    document.getElementById('alvo').innerHTML = '<a id="g" href="/x/" data-drawer="pedido:1"><span id="dentro">Pedido</span></a>'
    clicar(document.getElementById('dentro'))
    await assentar()
    expect(store.pilha.map(e => e.chave)).toEqual(['pedido:1'])
  })

  it('V8-OVL-081: data-drawer com el: abre o elemento da página com as opções dele', async () => {
    await comPagina(`
      <form id="demo-filtros" data-drawer-side="left" data-drawer-title="Filtros"><input name="q"></form>
      <button id="g" type="button" data-drawer="el:#demo-filtros">Filtrar</button>`)
    clicar(document.getElementById('g'))
    await assentar()
    const drawer = dialogos()[0]
    expect(drawer.classList.contains('v8-drawer-left')).toBe(true)
    expect(store.topo.titulo).toBe('Filtros')
    expect(drawer.contains(document.getElementById('demo-filtros'))).toBe(true)
    expect(painel()).toEqual([])
  })

  it('V8-OVL-082: data-modal abre o modal do registro', async () => {
    await comPagina('<a id="g" href="/v8/demo/clientes/7/" data-modal="resumo:7">Ampliar</a>')
    const evento = clicar(document.getElementById('g'))
    await assentar()
    expect(evento.defaultPrevented).toBe(true)
    expect(store.topo.kind).toBe('modal')
    expect(dialogos()[0].classList.contains('v8-modal-fullscreen')).toBe(true)
    expect(document.querySelector('[data-teste-botao="resumo"]').textContent).toBe('resumo 7')
  })

  it('V8-OVL-084: alvo que não pode ser aberto deixa o link seguir normalmente', async () => {
    await comPagina(`
      <a id="a" href="/v8/x/" data-drawer="desconhecido:1">A</a>
      <a id="b" href="/v8/x/" data-drawer="https://exemplo.invalid">B</a>
      <a id="c" href="/v8/x/" data-modal="nada:1">C</a>`)
    ;['a', 'b', 'c'].forEach(id => {
      expect(clicar(document.getElementById(id)).defaultPrevented, id).toBe(false)
    })
    await assentar()
    expect(store.entradas).toHaveLength(0)
  })

  it('V8-OVL-085: clique com tecla modificadora ou botão do meio não é interceptado', async () => {
    await comPagina('<a id="g" href="/v8/demo/clientes/42/" data-drawer="cliente:42">Ana</a>')
    const g = document.getElementById('g')
    expect(clicar(g, { ctrlKey: true }).defaultPrevented).toBe(false)
    expect(clicar(g, { metaKey: true }).defaultPrevented).toBe(false)
    expect(clicar(g, { shiftKey: true }).defaultPrevented).toBe(false)
    expect(clicar(g, { button: 1 }).defaultPrevented).toBe(false)
    await assentar()
    expect(store.entradas).toHaveLength(0)
  })

  it('V8-OVL-083: data-confirm em formulário pede confirmação e só então envia', async () => {
    await comPagina(`
      <form id="f" method="post" action="/v8/demo/clientes/arquivar/" data-confirm="Arquivar os selecionados?" data-confirm-title="Arquivar" data-confirm-ok="Arquivar">
        <button id="g" type="submit" class="v8-btn-perigo">Arquivar</button>
      </form>`)
    const formulario = document.getElementById('f')
    const envios = []
    // Ouvinte na janela: roda depois do ouvinte do documento, que é o dos gatilhos.
    const aoEnviar = e => {
      if (e.target === formulario) {
        envios.push(e.defaultPrevented)
        e.preventDefault()
      }
    }
    window.addEventListener('submit', aoEnviar)

    document.getElementById('g').click()
    await assentar()
    expect(envios).toEqual([true])
    expect(store.topo.type).toBe('confirm')
    expect(store.topo.titulo).toBe('Arquivar')
    expect(document.querySelector('.v8-confirm-mensagem').textContent.trim()).toBe('Arquivar os selecionados?')
    expect(document.querySelector('[data-confirm-botao=ok]').textContent.trim()).toBe('Arquivar')
    document.querySelector('[data-confirm-botao=cancelar]').click()
    await assentar()
    expect(envios).toEqual([true])

    document.getElementById('g').click()
    await assentar()
    expect(store.topo.type).toBe('confirm')
    ;[...document.querySelectorAll('[data-confirm-botao=ok]')].at(-1).click()
    await assentar()
    // O segundo envio, depois da confirmação, passa sem ser barrado.
    expect(envios).toEqual([true, true, false])
    window.removeEventListener('submit', aoEnviar)
  })

  it('V8-OVL-083: data-confirm em link segue o link depois de confirmar', async () => {
    const navegacao = (await import('~@/core/navegacao')).default
    navegacao.ir.mockClear()
    await comPagina('<a id="g" href="/v8/demo/limpar/" data-confirm="Limpar tudo?">Limpar</a>')
    const evento = clicar(document.getElementById('g'))
    await assentar()
    expect(evento.defaultPrevented).toBe(true)
    expect(navegacao.ir).not.toHaveBeenCalled()
    document.querySelector('[data-confirm-botao=ok]').click()
    await assentar()
    expect(navegacao.ir).toHaveBeenCalledTimes(1)
    expect(new URL(navegacao.ir.mock.calls[0][0]).pathname).toBe('/v8/demo/limpar/')
  })

  it('V8-OVL-104: a mensagem de data-confirm entra como texto', async () => {
    await comPagina('<a id="g" href="/x/" data-confirm="&lt;img src=x onerror=alert(1)&gt;">X</a>')
    clicar(document.getElementById('g'))
    await assentar()
    expect(dialogos()[0].querySelector('img')).toBeNull()
  })

  it('V8-DEMO-012: data-drawer-auto abre o painel sozinho em tela larga', async () => {
    vi.spyOn(window, 'matchMedia').mockImplementation(() => ({
      matches: true, addEventListener: () => {}, removeEventListener: () => {}
    }))
    await preparar()
    document.body.insertAdjacentHTML('beforeend', `
      <div data-v8-doca="left"></div>
      <form id="demo-filtros" data-drawer-auto data-drawer-side="left" data-drawer-mode="docked" data-drawer-mode-estreito="overlay" data-drawer-title="Filtros"></form>`)
    pararGatilhos = iniciarGatilhos()
    await assentar()
    const lateral = dialogos()[0]
    expect(lateral.getAttribute('role')).toBe('complementary')
    expect(document.querySelector('[data-v8-doca="left"]').contains(document.getElementById('demo-filtros'))).toBe(true)
    expect(store.pilha).toHaveLength(0)
  })
})
