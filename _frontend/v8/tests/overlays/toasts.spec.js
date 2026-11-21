import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'

import pinia from '~@/core/pinia'
import ToastHost from '~@/overlays/ToastHost.vue'
import { DURACOES, MAXIMO_VISIVEIS, useToastStore } from '~@/overlays/ToastStore'
import { nivelDaMensagem, toastsDasMensagens } from '~@/overlays/mensagens'
import { useToast } from '~@/overlays/useToast'

const XSS = '<img src=x onerror=alert(1)>'

let store = null
let montados = []

function montarHost() {
  const wrapper = mount(ToastHost, { attachTo: document.body })
  montados.push(wrapper)
  return wrapper
}

function toastsNaTela() {
  return [...document.querySelectorAll('.v8-toast')]
}

function textos(lista) {
  return lista.map(t => t.texto)
}

function escreverMensagens(texto) {
  const el = document.createElement('script')
  el.id = 'v8-messages'
  el.type = 'application/json'
  el.textContent = texto
  document.body.appendChild(el)
  return el
}

describe('toasts', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    store = useToastStore(pinia)
    store.limpar()
  })

  afterEach(() => {
    montados.forEach(wrapper => wrapper.unmount())
    montados = []
    store.limpar()
  })

  describe('useToast e fila', () => {
    it('V8-OVL-070: useToast() oferece success, info, warning e error, cada um com seu nível', () => {
      const toast = useToast()

      const ids = [
        toast.success('salvo'),
        toast.info('aviso geral'),
        toast.warning('atenção'),
        toast.error('falhou')
      ]

      expect(new Set(ids).size).toBe(4)
      expect(store.visiveis).toEqual([
        { id: ids[0], nivel: 'success', texto: 'salvo' },
        { id: ids[1], nivel: 'info', texto: 'aviso geral' },
        { id: ids[2], nivel: 'warning', texto: 'atenção' },
        { id: ids[3], nivel: 'error', texto: 'falhou' }
      ])
      expect(store.fila).toEqual([])
    })

    it('V8-OVL-070: funciona fora de componente e usa o mesmo store do host', async () => {
      montarHost()

      useToast().info('vindo de fora')
      await nextTick()

      expect(toastsNaTela()).toHaveLength(1)
      expect(toastsNaTela()[0].textContent).toContain('vindo de fora')
    })

    it('V8-OVL-070: no máximo quatro ficam visíveis, e os demais aguardam em fila', () => {
      const toast = useToast()

      for (let i = 1; i <= 7; i += 1) {
        toast.error(`erro ${i}`)
      }

      expect(MAXIMO_VISIVEIS).toBe(4)
      expect(textos(store.visiveis)).toEqual(['erro 1', 'erro 2', 'erro 3', 'erro 4'])
      expect(textos(store.fila)).toEqual(['erro 5', 'erro 6', 'erro 7'])
    })

    it('V8-OVL-070: ao sair um visível, entra o primeiro da fila', () => {
      const toast = useToast()
      const ids = []
      for (let i = 1; i <= 6; i += 1) {
        ids.push(toast.error(`erro ${i}`))
      }

      toast.dismiss(ids[1])

      expect(textos(store.visiveis)).toEqual(['erro 1', 'erro 3', 'erro 4', 'erro 5'])
      expect(textos(store.fila)).toEqual(['erro 6'])
    })

    it('V8-OVL-070: dismiss() também retira um toast que ainda está na fila', () => {
      const toast = useToast()
      const ids = []
      for (let i = 1; i <= 6; i += 1) {
        ids.push(toast.error(`erro ${i}`))
      }

      toast.dismiss(ids[4])

      expect(textos(store.visiveis)).toEqual(['erro 1', 'erro 2', 'erro 3', 'erro 4'])
      expect(textos(store.fila)).toEqual(['erro 6'])
      expect(() => toast.dismiss(999999)).not.toThrow()
    })

    it('V8-OVL-070: o host mostra os toasts na camada --z-toast, quatro por vez', async () => {
      montarHost()
      const toast = useToast()
      for (let i = 1; i <= 6; i += 1) {
        toast.error(`erro ${i}`)
      }
      await nextTick()

      const containers = document.querySelectorAll('.v8-toasts')
      expect(containers).toHaveLength(1)
      const container = containers[0]
      expect(container.closest('body')).toBe(document.body)
      expect(container.classList.contains('z-(--z-toast)')).toBe(true)
      expect(container.getAttribute('aria-label')).toBe('Notificações')
      expect(container.hasAttribute('style')).toBe(false)
      expect(toastsNaTela()).toHaveLength(4)
      expect(toastsNaTela().every(el => container.contains(el))).toBe(true)
    })

    it('V8-OVL-070: o botão Dispensar retira o toast e traz o próximo da fila', async () => {
      montarHost()
      const toast = useToast()
      for (let i = 1; i <= 5; i += 1) {
        toast.error(`erro ${i}`)
      }
      await nextTick()

      const botao = toastsNaTela()[0].querySelector('button[aria-label="Dispensar"]')
      expect(botao).not.toBeNull()
      expect(botao.getAttribute('type')).toBe('button')
      botao.click()
      await nextTick()

      expect(toastsNaTela().map(el => el.querySelector('p:last-of-type').textContent.trim()))
        .toEqual(['erro 2', 'erro 3', 'erro 4', 'erro 5'])
      expect(store.fila).toEqual([])
    })
  })

  describe('contagem', () => {
    it.each([
      ['success', 4000],
      ['info', 5000],
      ['warning', 7000]
    ])('V8-OVL-071: o toast %s some sozinho após %i ms', (nivel, duracao) => {
      expect(DURACOES[nivel]).toBe(duracao)
      useToast()[nivel]('texto')

      vi.advanceTimersByTime(duracao - 1)
      expect(store.visiveis).toHaveLength(1)

      vi.advanceTimersByTime(1)
      expect(store.visiveis).toHaveLength(0)
    })

    it('V8-OVL-071: o toast de erro não some sozinho', () => {
      expect(DURACOES.error).toBeNull()
      const toast = useToast()
      const id = toast.error('falhou')

      vi.advanceTimersByTime(24 * 60 * 60 * 1000)
      expect(textos(store.visiveis)).toEqual(['falhou'])
      expect(vi.getTimerCount()).toBe(0)

      toast.dismiss(id)
      expect(store.visiveis).toEqual([])
    })

    it('V8-OVL-071: duracao informada vale no lugar do tempo do nível', () => {
      const toast = useToast()
      toast.success('rápido', { duracao: 1000 })
      toast.error('erro com prazo', { duracao: 2000 })
      toast.info('fixo', { duracao: null })

      vi.advanceTimersByTime(1000)
      expect(textos(store.visiveis)).toEqual(['erro com prazo', 'fixo'])

      vi.advanceTimersByTime(1000)
      expect(textos(store.visiveis)).toEqual(['fixo'])

      vi.advanceTimersByTime(60 * 60 * 1000)
      expect(textos(store.visiveis)).toEqual(['fixo'])
    })

    it('V8-OVL-071: a contagem de quem está na fila só começa ao entrar na tela', () => {
      const toast = useToast()
      const erros = []
      for (let i = 1; i <= 4; i += 1) {
        erros.push(toast.error(`erro ${i}`))
      }
      toast.success('da fila')

      // Passa muito mais do que o tempo do nível enquanto ele aguarda.
      vi.advanceTimersByTime(60000)
      expect(textos(store.fila)).toEqual(['da fila'])

      toast.dismiss(erros[0])
      expect(textos(store.visiveis)).toContain('da fila')

      vi.advanceTimersByTime(3999)
      expect(textos(store.visiveis)).toContain('da fila')

      vi.advanceTimersByTime(1)
      expect(textos(store.visiveis)).not.toContain('da fila')
    })

    it('V8-OVL-071: pausar guarda o tempo restante, e retomar continua dele', () => {
      const id = useToast().success('texto')

      vi.advanceTimersByTime(3000)
      store.pausar(id)
      store.pausar(id)

      vi.advanceTimersByTime(60000)
      expect(store.visiveis).toHaveLength(1)

      store.retomar(id)
      store.retomar(id)
      vi.advanceTimersByTime(999)
      expect(store.visiveis).toHaveLength(1)

      vi.advanceTimersByTime(1)
      expect(store.visiveis).toHaveLength(0)
    })

    it('V8-OVL-071: a contagem pausa com o ponteiro sobre o toast', async () => {
      montarHost()
      useToast().info('texto')
      await nextTick()
      const el = toastsNaTela()[0]

      vi.advanceTimersByTime(4000)
      el.dispatchEvent(new MouseEvent('mouseenter'))
      vi.advanceTimersByTime(60000)
      expect(store.visiveis).toHaveLength(1)

      el.dispatchEvent(new MouseEvent('mouseleave'))
      vi.advanceTimersByTime(999)
      expect(store.visiveis).toHaveLength(1)

      vi.advanceTimersByTime(1)
      expect(store.visiveis).toHaveLength(0)
      await nextTick()
      expect(toastsNaTela()).toHaveLength(0)
    })

    it('V8-OVL-071: a contagem pausa com o foco dentro do toast', async () => {
      montarHost()
      useToast().warning('texto')
      await nextTick()
      const botao = toastsNaTela()[0].querySelector('button')

      vi.advanceTimersByTime(6000)
      botao.dispatchEvent(new FocusEvent('focusin', { bubbles: true }))
      vi.advanceTimersByTime(60000)
      expect(store.visiveis).toHaveLength(1)

      botao.dispatchEvent(new FocusEvent('focusout', { bubbles: true }))
      vi.advanceTimersByTime(999)
      expect(store.visiveis).toHaveLength(1)

      vi.advanceTimersByTime(1)
      expect(store.visiveis).toHaveLength(0)
    })

    it('V8-OVL-071: com ponteiro e foco, a contagem só volta quando os dois saem', async () => {
      montarHost()
      useToast().success('texto')
      await nextTick()
      const el = toastsNaTela()[0]
      const botao = el.querySelector('button')

      el.dispatchEvent(new MouseEvent('mouseenter'))
      botao.dispatchEvent(new FocusEvent('focusin', { bubbles: true }))
      el.dispatchEvent(new MouseEvent('mouseleave'))
      vi.advanceTimersByTime(60000)
      expect(store.visiveis).toHaveLength(1)

      botao.dispatchEvent(new FocusEvent('focusout', { bubbles: true }))
      vi.advanceTimersByTime(3999)
      expect(store.visiveis).toHaveLength(1)

      vi.advanceTimersByTime(1)
      expect(store.visiveis).toHaveLength(0)
    })
  })

  describe('acessibilidade', () => {
    it('V8-OVL-072: o toast usa role="status", e o de erro, role="alert"', async () => {
      montarHost()
      const toast = useToast()
      toast.success('a')
      toast.info('b')
      toast.warning('c')
      toast.error('d')
      await nextTick()

      expect(toastsNaTela().map(el => el.getAttribute('role')))
        .toEqual(['status', 'status', 'status', 'alert'])
      expect(toastsNaTela().map(el => [...el.classList].find(c => c.startsWith('v8-toast-'))))
        .toEqual(['v8-toast-success', 'v8-toast-info', 'v8-toast-warning', 'v8-toast-error'])
    })
  })

  describe('mensagens do Django', () => {
    it('V8-OVL-073: cada mensagem de #v8-messages vira um toast do nível correspondente', () => {
      escreverMensagens(JSON.stringify([
        { nivel: 'success', texto: 'Registro salvo.' },
        { nivel: 'info', texto: 'Sessão aberta.' },
        { nivel: 'warning', texto: 'Prazo próximo.' },
        { nivel: 'error', texto: 'Falha ao salvar.' },
        { nivel: 'debug', texto: 'Depuração.' }
      ]))

      expect(toastsDasMensagens()).toBe(5)

      expect(store.visiveis.map(t => [t.nivel, t.texto])).toEqual([
        ['success', 'Registro salvo.'],
        ['info', 'Sessão aberta.'],
        ['warning', 'Prazo próximo.'],
        ['error', 'Falha ao salvar.']
      ])
      expect(store.fila.map(t => [t.nivel, t.texto])).toEqual([['info', 'Depuração.']])
    })

    it.each([
      ['debug', 'info'],
      ['info', 'info'],
      ['success', 'success'],
      ['warning', 'warning'],
      ['error', 'error'],
      ['ERROR', 'error'],
      ['alert-dismissible error', 'error'],
      ['minha-tag warning error', 'warning'],
      ['  success  ', 'success'],
      ['danger', 'info'],
      ['', 'info'],
      [null, 'info'],
      [undefined, 'info'],
      [40, 'info'],
      ['constructor', 'info'],
      ['dismiss', 'info']
    ])('V8-OVL-073: a tag de nível %j vira %s', (tag, esperado) => {
      expect(nivelDaMensagem(tag)).toBe(esperado)
    })

    it('V8-OVL-073: sem #v8-messages nenhum toast é criado', () => {
      expect(toastsDasMensagens()).toBe(0)
      expect(store.visiveis).toEqual([])
    })

    it.each([
      ['JSON inválido', '[{"nivel": "info", "texto": '],
      ['script vazio', ''],
      ['objeto', '{"nivel": "info", "texto": "x"}'],
      ['texto', '"mensagem"'],
      ['null', 'null']
    ])('V8-OVL-073: %s em #v8-messages é ignorado, sem exceção', (_caso, conteudo) => {
      escreverMensagens(conteudo)

      expect(toastsDasMensagens()).toBe(0)
      expect(store.visiveis).toEqual([])
    })

    it('V8-OVL-073: item sem texto é ignorado e não conta', () => {
      escreverMensagens(JSON.stringify([
        { nivel: 'error' },
        { nivel: 'error', texto: '' },
        { nivel: 'error', texto: '   ' },
        { nivel: 'error', texto: null },
        { nivel: 'error', texto: { html: 'x' } },
        null,
        'solta',
        { texto: 'sem nível' },
        { nivel: 'success', texto: 'válida' }
      ]))

      expect(toastsDasMensagens()).toBe(2)
      expect(store.visiveis.map(t => [t.nivel, t.texto])).toEqual([
        ['info', 'sem nível'],
        ['success', 'válida']
      ])
    })
  })

  describe('segurança', () => {
    it('V8-OVL-104: texto de toast com HTML aparece como texto e não cria elemento', async () => {
      montarHost()
      useToast().error(XSS)
      await nextTick()

      const el = toastsNaTela()[0]
      expect(el.textContent).toContain(XSS)
      expect(document.querySelector('img')).toBeNull()
      expect(el.innerHTML).toContain('&lt;img')
    })

    it('V8-OVL-104: mensagem de #v8-messages com HTML aparece como texto', async () => {
      montarHost()
      escreverMensagens(JSON.stringify([
        { nivel: 'warning', texto: XSS },
        { nivel: '<b>error</b>', texto: '<script>alert(1)</script>' }
      ]))

      expect(toastsDasMensagens()).toBe(2)
      await nextTick()

      const [primeiro, segundo] = toastsNaTela()
      expect(primeiro.textContent).toContain(XSS)
      expect(segundo.textContent).toContain('<script>alert(1)</script>')
      expect(segundo.getAttribute('role')).toBe('status')
      expect(document.querySelector('img')).toBeNull()
      expect(document.querySelector('.v8-toasts script')).toBeNull()
      expect(document.querySelector('.v8-toasts b')).toBeNull()
    })
  })
})
