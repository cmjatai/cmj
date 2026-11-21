import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { assentar, conteudoDeTeste, dialogos, montarHost, novoStore, tecla } from './apoio'

let store
let host

beforeEach(() => {
  store = novoStore()
  host = montarHost()
})

afterEach(() => {
  host.unmount()
  store.$limpar()
})

describe('pilha de overlays', () => {
  it('V8-OVL-010: drawers e modals entram na mesma pilha, na ordem de abertura', async () => {
    store.openDrawer({ componente: conteudoDeTeste({}, 'a') }, { title: 'A' })
    store.openModal(conteudoDeTeste({}, 'b'), {}, { title: 'B' })
    await assentar()
    expect(store.pilha.map(e => e.kind)).toEqual(['drawer', 'modal'])
    expect(store.topo.titulo).toBe('B')
    expect(dialogos()).toHaveLength(2)
  })

  it('V8-OVL-020: o overlay é desenhado no body, fora do elemento do app', async () => {
    store.openModal(conteudoDeTeste(), {}, { title: 'No body' })
    await assentar()
    const dialogo = dialogos()[0]
    expect(dialogo.closest('body')).toBe(document.body)
    expect(host.element.contains?.(dialogo) || false).toBe(false)
  })

  it('V8-OVL-023: dialog com aria-modal e rótulo; o confirm é alertdialog', async () => {
    store.openModal(conteudoDeTeste(), {}, { title: 'Editar cliente' })
    await assentar()
    const dialogo = dialogos()[0]
    expect(dialogo.getAttribute('role')).toBe('dialog')
    expect(dialogo.getAttribute('aria-modal')).toBe('true')
    const rotulo = document.getElementById(dialogo.getAttribute('aria-labelledby'))
    expect(rotulo.textContent.trim()).toBe('Editar cliente')

    store.confirm({ titulo: 'Apagar?', mensagem: 'Sem volta.' })
    await assentar()
    expect(dialogos()[1].getAttribute('role')).toBe('alertdialog')
  })

  it('V8-OVL-011: ESC fecha só o topo da pilha', async () => {
    store.openDrawer({ componente: conteudoDeTeste({}, 'a') }, { title: 'A' })
    await assentar()
    store.openModal(conteudoDeTeste({}, 'b'), {}, { title: 'B' })
    await assentar()
    tecla('Escape')
    await assentar()
    expect(store.pilha.map(e => e.titulo)).toEqual(['A'])
    tecla('Escape')
    await assentar()
    expect(store.pilha).toHaveLength(0)
  })

  it('V8-OVL-011: o botão de fechar de um overlay age nele, e clique fora só no topo', async () => {
    store.openDrawer({ componente: conteudoDeTeste({}, 'a') }, { title: 'A' })
    await assentar()
    store.openModal(conteudoDeTeste({}, 'b'), {}, { title: 'B' })
    await assentar()
    expect(dialogos()[1].hasAttribute('data-overlay-topo')).toBe(true)
    expect(dialogos()[0].hasAttribute('data-overlay-topo')).toBe(false)
    dialogos()[1].querySelector('[data-overlay-fechar]').click()
    await assentar()
    expect(store.pilha.map(e => e.titulo)).toEqual(['A'])
  })

  it('V8-OVL-012: fechar um overlay fecha antes os que estão acima', async () => {
    const ordem = []
    const a = store.openDrawer({ componente: conteudoDeTeste({}, 'a') }, { title: 'A' }).then(() => ordem.push('a'))
    const b = store.openModal(conteudoDeTeste({}, 'b'), {}, { title: 'B' }).then(() => ordem.push('b'))
    await assentar()
    store.close(store.pilha[0].id, 'x')
    await Promise.all([a, b])
    expect(ordem).toEqual(['b', 'a'])
    expect(store.pilha).toHaveLength(0)
  })

  it('V8-OVL-021: o foco entra no overlay e volta ao gatilho ao fechar', async () => {
    const gatilho = document.createElement('button')
    document.body.append(gatilho)
    gatilho.focus()
    expect(document.activeElement).toBe(gatilho)
    store.openModal(conteudoDeTeste(), {}, { title: 'Foco' })
    await assentar()
    const dialogo = dialogos()[0]
    expect(dialogo.contains(document.activeElement)).toBe(true)
    store.close(store.topo.id)
    await assentar()
    expect(document.activeElement).toBe(gatilho)
  })

  it('V8-OVL-022: a página atrás fica oculta para leitores de tela e sem cliques', async () => {
    const pagina = document.createElement('main')
    pagina.innerHTML = '<a href="#x">link da página</a>'
    document.body.append(pagina)
    store.openModal(conteudoDeTeste(), {}, { title: 'Modal' })
    await assentar()
    expect(pagina.getAttribute('aria-hidden')).toBe('true')
    expect(document.body.style.pointerEvents).toBe('none')
    store.close(store.topo.id)
    await assentar()
    expect(pagina.hasAttribute('aria-hidden')).toBe(false)
    expect(document.body.style.pointerEvents).not.toBe('none')
  })

  it('V8-OVL-003: um drawer aberto sobre um modal fica na camada do modal', async () => {
    store.openDrawer({ componente: conteudoDeTeste({}, 'a') }, { title: 'A' })
    await assentar()
    expect(dialogos()[0].classList.contains('v8-camada-drawer')).toBe(true)
    store.openModal(conteudoDeTeste({}, 'b'), {}, { title: 'B' })
    store.openDrawer({ componente: conteudoDeTeste({}, 'c') }, { title: 'C' })
    await assentar()
    const [, modal, drawer] = dialogos()
    expect(modal.classList.contains('v8-camada-modal')).toBe(true)
    expect(drawer.classList.contains('v8-camada-modal')).toBe(true)
    expect(Number(drawer.style.getPropertyValue('--v8-ordem')))
      .toBeGreaterThan(Number(modal.style.getPropertyValue('--v8-ordem')))
  })

  it('V8-OVL-034: drawers do mesmo lado ficam deslocados sob o do topo', async () => {
    store.openDrawer({ componente: conteudoDeTeste({}, 'a') }, { title: 'A', side: 'right' })
    store.openDrawer({ componente: conteudoDeTeste({}, 'b') }, { title: 'B', side: 'right' })
    store.openDrawer({ componente: conteudoDeTeste({}, 'c') }, { title: 'C', side: 'left' })
    await assentar()
    const [a, b, c] = dialogos()
    expect(a.style.getPropertyValue('--v8-profundidade')).toBe('1')
    expect(b.style.getPropertyValue('--v8-profundidade')).toBe('0')
    expect(c.style.getPropertyValue('--v8-profundidade')).toBe('0')
  })
})

describe('guarda de alterações', () => {
  it('V8-OVL-024: overlay alterado pede confirmação antes de fechar', async () => {
    const controles = {}
    let resolvido = 'aberto'
    store.openModal(conteudoDeTeste(controles, 'form'), {}, { title: 'Form' }).then(v => {
      resolvido = v
    })
    await assentar()
    controles.form.setDirty(true)
    tecla('Escape')
    await assentar()
    // Abriu a confirmação por cima, e o modal continua lá.
    expect(store.pilha).toHaveLength(2)
    expect(store.topo.type).toBe('confirm')
    document.querySelector('[data-confirm-botao=cancelar]').click()
    await assentar()
    expect(store.pilha.map(e => e.titulo)).toEqual(['Form'])
    expect(resolvido).toBe('aberto')

    tecla('Escape')
    await assentar()
    document.querySelector('[data-confirm-botao=ok]').click()
    await assentar()
    expect(store.pilha).toHaveLength(0)
    expect(resolvido).toBeUndefined()
  })

  it('V8-OVL-024: sem alteração, fecha direto', async () => {
    store.openModal(conteudoDeTeste(), {}, { title: 'Form' })
    await assentar()
    tecla('Escape')
    await assentar()
    expect(store.pilha).toHaveLength(0)
  })

  it('V8-OVL-025: com overlay alterado, sair da página dispara o aviso do navegador', async () => {
    const controles = {}
    store.openModal(conteudoDeTeste(controles, 'form'), {}, { title: 'Form' })
    await assentar()
    const semAlteracao = new Event('beforeunload', { cancelable: true })
    window.dispatchEvent(semAlteracao)
    expect(semAlteracao.defaultPrevented).toBe(false)
    controles.form.setDirty(true)
    const comAlteracao = new Event('beforeunload', { cancelable: true })
    window.dispatchEvent(comAlteracao)
    expect(comAlteracao.defaultPrevented).toBe(true)
  })
})

describe('modals por Promise', () => {
  it('V8-OVL-060: confirm resolve true ao confirmar e false ao cancelar ou dispensar', async () => {
    const { useModal } = await import('~@/overlays/useModal')
    const { confirm } = useModal()

    let resultado = confirm({ titulo: 'Arquivar?', mensagem: 'Arquivar 3 clientes?' })
    await assentar()
    expect(document.querySelector('.v8-confirm-mensagem').textContent.trim()).toBe('Arquivar 3 clientes?')
    document.querySelector('[data-confirm-botao=ok]').click()
    expect(await resultado).toBe(true)

    resultado = confirm({ mensagem: 'De novo?' })
    await assentar()
    document.querySelector('[data-confirm-botao=cancelar]').click()
    expect(await resultado).toBe(false)

    resultado = confirm({ mensagem: 'E agora?' })
    await assentar()
    tecla('Escape')
    expect(await resultado).toBe(false)
  })

  it('V8-OVL-061: openModal resolve com o valor de close e com undefined ao dispensar', async () => {
    const { useModal } = await import('~@/overlays/useModal')
    const { openModal } = useModal()
    const controles = {}

    let resultado = openModal(conteudoDeTeste(controles, 'm'), { texto: 'oi' }, { title: 'M' })
    await assentar()
    expect(document.querySelector('[data-teste-botao="m"]').textContent).toBe('oi')
    controles.m.close({ id: 7 })
    expect(await resultado).toEqual({ id: 7 })

    resultado = openModal(conteudoDeTeste(controles, 'm'), {}, { title: 'M' })
    await assentar()
    controles.m.dismiss()
    expect(await resultado).toBeUndefined()
  })

  it('V8-OVL-062: o conteúdo controla o próprio overlay por useOverlay', async () => {
    const controles = {}
    store.openModal(conteudoDeTeste(controles, 'm'), {}, { title: 'Antes' })
    await assentar()
    expect(Object.keys(controles.m)).toEqual(expect.arrayContaining(['close', 'dismiss', 'setDirty', 'setTitle']))
    controles.m.setTitle('Depois')
    await assentar()
    expect(store.topo.titulo).toBe('Depois')
    const dialogo = dialogos()[0]
    expect(document.getElementById(dialogo.getAttribute('aria-labelledby')).textContent.trim()).toBe('Depois')
  })

  it('V8-OVL-063: o componente do modal é importado sob demanda', async () => {
    let importou = 0
    const carregador = () => {
      importou += 1
      return Promise.resolve({ default: conteudoDeTeste({}, 'lazy') })
    }
    expect(importou).toBe(0)
    store.openModal(carregador, {}, { title: 'Lazy' })
    await assentar()
    expect(importou).toBe(1)
    expect(document.querySelector('[data-teste="lazy"]')).not.toBeNull()
  })

  it('V8-OVL-041: falha ao carregar mostra erro com nova tentativa, dentro do overlay', async () => {
    let tentativas = 0
    const carregador = () => {
      tentativas += 1
      return tentativas === 1
        ? Promise.reject(new Error('rede'))
        : Promise.resolve({ default: conteudoDeTeste({}, 'lazy') })
    }
    store.openModal(carregador, {}, { title: 'Lazy' })
    await assentar()
    const dialogo = dialogos()[0]
    expect(dialogo.querySelector('[role="alert"]')).not.toBeNull()
    dialogo.querySelector('[role="alert"] button').click()
    await assentar()
    expect(dialogo.querySelector('[data-teste="lazy"]')).not.toBeNull()
  })

  it('V8-OVL-067: o modal fullscreen ocupa a janela e segue as regras de modal', async () => {
    const { useModal } = await import('~@/overlays/useModal')
    useModal().openFullscreen(conteudoDeTeste(), {}, { title: 'Tela cheia' })
    await assentar()
    const dialogo = dialogos()[0]
    expect(dialogo.classList.contains('v8-modal-fullscreen')).toBe(true)
    expect(dialogo.getAttribute('aria-modal')).toBe('true')
  })

  it('V8-OVL-104: título e mensagem entram como texto, nunca como HTML', async () => {
    const hostil = '<img src=x onerror=alert(1)>'
    store.confirm({ titulo: hostil, mensagem: hostil })
    await assentar()
    const dialogo = dialogos()[0]
    expect(dialogo.querySelector('img')).toBeNull()
    expect(dialogo.querySelector('.v8-confirm-mensagem').textContent.trim()).toBe(hostil)
    expect(dialogo.querySelector('.v8-overlay-titulo').textContent.trim()).toBe(hostil)
  })
})
