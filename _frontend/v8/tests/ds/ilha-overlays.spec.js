// Ilha `ds-overlays` da vitrine do design system (docs/specs/v8/ds.md).
import fs from 'fs'
import path from 'path'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { HttpError } from '~@/http/client'
import { ilhas } from '~@/core/ilhas'
import DsOverlays from '~@/modules/ds/ilhas/DsOverlays.vue'
import AmostraForm from '~@/modules/ds/modais/AmostraForm.vue'
import { enviarAmostra, passosDoAssistente, validarBairro } from '~@/modules/ds/amostras'
import {
  assentar,
  comOverlay,
  fecharOverlay,
  limparStores,
  overlayDeMentira,
  overlaysAbertos,
  toasts
} from '../demo/apoio'

const PASTA_DS = path.resolve(__dirname, '../../src/modules/ds')

function montar() {
  return mount(DsOverlays, { attachTo: document.body })
}

async function clicar(wrapper, seletor) {
  await wrapper.find(seletor).trigger('click')
  await assentar()
}

function resultado(wrapper) {
  return wrapper.find('[data-ds-resultado]').text()
}

describe('ilha ds-overlays', () => {
  let fetch

  beforeEach(() => {
    fetch = vi.fn(() => Promise.reject(new Error('rede proibida no teste')))
    vi.stubGlobal('fetch', fetch)
  })

  afterEach(() => {
    limparStores()
    vi.unstubAllGlobals()
  })

  it('V8-DS-009: a ilha está no registro e abre cada tipo de modal', async () => {
    expect(Object.hasOwn(ilhas, 'ds-overlays')).toBe(true)
    const wrapper = montar()

    const esperado = [
      ['[data-ds-acao="confirmar"]', 'confirm'],
      ['[data-ds-acao="confirmar-perigo"]', 'confirm'],
      ['[data-ds-acao="modal"]', 'default'],
      ['[data-ds-acao="formulario"]', 'form'],
      ['[data-ds-acao="assistente"]', 'wizard'],
      ['[data-ds-acao="tela-cheia"]', 'fullscreen']
    ]
    for (const [seletor, tipo] of esperado) {
      await clicar(wrapper, seletor)
      const abertos = overlaysAbertos()
      expect(abertos.length, seletor).toBe(1)
      expect(abertos[0].kind).toBe('modal')
      expect(abertos[0].type, seletor).toBe(tipo)
      fecharOverlay(abertos[0].id, tipo === 'confirm' ? true : undefined)
      await assentar()
      expect(overlaysAbertos()).toEqual([])
    }
    expect(resultado(wrapper)).toBe('Tela cheia fechada.')

    await clicar(wrapper, '[data-ds-acao="confirmar-perigo"]')
    expect(overlaysAbertos()[0].opcoes.variante).toBe('perigo')
    fecharOverlay(overlaysAbertos()[0].id, false)
    await assentar()
    expect(resultado(wrapper)).toBe('Cancelado.')
    wrapper.unmount()
  })

  it('V8-DS-009: os quatro níveis de toast', async () => {
    const wrapper = montar()
    for (const nivel of ['success', 'info', 'warning', 'error']) {
      await clicar(wrapper, `[data-ds-toast="${nivel}"]`)
    }
    expect(toasts().map(t => t.nivel)).toEqual(['success', 'info', 'warning', 'error'])
    wrapper.unmount()
  })

  it('V8-DS-009: o formulário de amostra mostra o erro junto ao campo e fecha com os dados', async () => {
    const overlay = overlayDeMentira()
    const wrapper = mount(AmostraForm, {
      global: { provide: comOverlay(overlay) },
      attachTo: document.body
    })
    await wrapper.find('form').trigger('submit')
    await assentar()
    expect(wrapper.text()).toContain('Informe ao menos três letras.')
    expect(overlay.close).not.toHaveBeenCalled()

    const [nome, email] = wrapper.findAll('input')
    await nome.setValue('Ana Lima')
    await email.setValue('ana.lima@exemplo.invalid')
    await wrapper.find('form').trigger('submit')
    await assentar()
    expect(overlay.close).toHaveBeenCalledWith({ nome: 'Ana Lima', email: 'ana.lima@exemplo.invalid' })
    wrapper.unmount()
  })

  it('V8-DS-009: a validação de amostra responde como o servidor', async () => {
    await expect(enviarAmostra({ nome: '', email: '' })).rejects.toBeInstanceOf(HttpError)
    await expect(enviarAmostra({ nome: '', email: '' })).rejects.toMatchObject({ codigo: 'validacao' })
    await expect(enviarAmostra({ nome: 'Ana', email: 'a@exemplo.invalid', bairro: 'Centro' })).resolves.toEqual({
      nome: 'Ana',
      email: 'a@exemplo.invalid',
      bairro: 'Centro'
    })
    expect(validarBairro({ bairro: '' })).toEqual({ bairro: ['Escolha um bairro.'] })
    expect(passosDoAssistente.map(p => p.titulo)).toEqual(['Identificação', 'Bairro'])
  })

  it('V8-DS-044: as ilhas do design system não fazem requisição', async () => {
    const wrapper = montar()
    for (const botao of wrapper.findAll('button')) {
      await botao.trigger('click')
      await assentar()
      overlaysAbertos().forEach(entrada => fecharOverlay(entrada.id, true))
      await assentar()
    }
    expect(fetch).not.toHaveBeenCalled()
    wrapper.unmount()

    const fontes = []
    const ler = pasta =>
      fs.readdirSync(pasta, { withFileTypes: true }).forEach(item => {
        const caminho = path.join(pasta, item.name)
        if (item.isDirectory()) {
          ler(caminho)
        } else {
          fontes.push([caminho, fs.readFileSync(caminho, 'utf8')])
        }
      })
    ler(PASTA_DS)
    expect(fontes.length).toBeGreaterThan(3)
    fontes.forEach(([caminho, fonte]) => {
      expect(fonte, caminho).not.toMatch(/\bfetch\(|XMLHttpRequest|\bhttp\.(get|post|put|patch|delete)\(|Resources\.|WebSocket/)
      expect(fonte, caminho).not.toMatch(/import http\b/)
    })
  })
})
