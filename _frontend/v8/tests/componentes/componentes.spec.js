// Componentes base sobre o Reka UI (docs/specs/v8/componentes.md).
import fs from 'fs'
import path from 'path'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, h, nextTick, ref } from 'vue'
import { DialogContent, DialogPortal, DialogRoot, DialogTitle } from 'reka-ui'
import Abas from '~@/componentes/Abas.vue'
import CaixaMarcacao from '~@/componentes/CaixaMarcacao.vue'
import Chave from '~@/componentes/Chave.vue'
import Dica from '~@/componentes/Dica.vue'
import GrupoOpcoes from '~@/componentes/GrupoOpcoes.vue'
import MenuSuspenso from '~@/componentes/MenuSuspenso.vue'
import Popover from '~@/componentes/Popover.vue'
import Sanfona from '~@/componentes/Sanfona.vue'
import Selecao from '~@/componentes/Selecao.vue'
import { ilhas } from '~@/core/ilhas'
import DsComponentes from '~@/modules/ds/ilhas/DsComponentes.vue'
import { assentar } from '../demo/apoio'
import { CSS_DOS_COMPONENTES, OFICIAL, PASTA, PRIMITIVAS, SO_EXIBICAO, desmontarTodos, fonte, ler, montar } from './apoio'

const OPCOES = [
  { valor: 'centro', rotulo: 'Centro' },
  { valor: 'norte', rotulo: 'Norte' },
  { valor: 'sul', rotulo: 'Sul' }
]

describe('componentes base', () => {
  afterEach(desmontarTodos)

  it('V8-CMP-001: os componentes base ficam em src/componentes, cada um sobre a sua primitiva do Reka UI', () => {
    const arquivos = fs.readdirSync(PASTA).filter(f => f.endsWith('.vue')).map(f => f.replace('.vue', '')).sort()
    expect(arquivos).toEqual(Object.keys(PRIMITIVAS).sort())
    const prefixos = Object.values(PRIMITIVAS).flat()
    Object.entries(PRIMITIVAS).forEach(([nome, primitivas]) => {
      const importados = /import\s*\{([^}]+)\}\s*from\s*'reka-ui'/.exec(fonte(nome))[1]
      const partes = importados.split(',').map(p => p.trim()).filter(Boolean)
      expect(partes.length, nome).toBeGreaterThan(0)
      // Cada parte é da primitiva do componente, pelo prefixo mais longo que casa
      // (ToggleGroup começa por Toggle, e ColorSwatchPicker por ColorSwatch).
      partes.forEach(parte => {
        const dona = prefixos.filter(p => parte.startsWith(p)).sort((a, b) => b.length - a.length)[0]
        expect([primitivas].flat(), `${nome}: ${parte}`).toContain(dona)
      })
    })
  })

  it('V8-CMP-002: invólucro fino, com v-model e sem requisição', async () => {
    Object.keys(PRIMITIVAS).forEach(nome => {
      const codigo = fonte(nome)
      expect(codigo, nome).not.toMatch(/\bfetch\(|XMLHttpRequest|http\/client|Resources\.|useGlobalStore|useAuthStore/)
      if (!SO_EXIBICAO.includes(nome)) {
        expect(codigo, nome).toMatch(/defineModel|defineEmits/)
      }
    })

    const chave = montar(Chave, { props: { rotulo: 'Avisar', modelValue: false } })
    await chave.find('[role="switch"]').trigger('click')
    expect(chave.emitted('update:modelValue')).toEqual([[true]])

    const caixa = montar(CaixaMarcacao, { props: { rotulo: 'Aceito', modelValue: false } })
    await caixa.find('[role="checkbox"]').trigger('click')
    expect(caixa.emitted('update:modelValue')).toEqual([[true]])

    const menu = montar(MenuSuspenso, {
      props: { open: true, itens: [{ valor: 'editar', rotulo: 'Editar' }] }
    })
    await assentar()
    document.querySelector('[role="menuitem"]').click()
    await assentar()
    expect(menu.emitted('selecionar')).toEqual([['editar']])
  })

  it('V8-CMP-003: o visual vem de classes v8-* e os estados dos atributos do Reka UI', async () => {
    const css = CSS_DOS_COMPONENTES.map(arquivo => ler(path.join(OFICIAL, arquivo))).join('\n')
    const definidas = new Set(
      [...CSS_DOS_COMPONENTES, 'componentes.css', 'shell.css']
        .flatMap(arquivo => [...ler(path.join(OFICIAL, arquivo)).matchAll(/\.(v8-[a-z0-9-]+)/g)].map(m => m[1]))
    )
    Object.keys(PRIMITIVAS).forEach(nome => {
      ;[...fonte(nome).matchAll(/\b(v8-[a-z0-9-]+)/g)].forEach(m => {
        expect(definidas.has(m[1]), `${nome}: ${m[1]}`).toBe(true)
      })
    })
    ;['data-state="checked"', 'data-state="active"', 'data-state="open"', '[data-highlighted]', '[data-disabled]', '[data-placeholder]'].forEach(
      estado => expect(css).toContain(estado)
    )

    const caixa = montar(CaixaMarcacao, { props: { modelValue: true, rotulo: 'Marcada' } })
    expect(caixa.find('.v8-caixa').attributes('data-state')).toBe('checked')
    await caixa.setProps({ modelValue: 'indeterminate' })
    expect(caixa.find('.v8-caixa').attributes('data-state')).toBe('indeterminate')

    const abas = montar(Abas, { props: { itens: OPCOES, modelValue: 'norte' } })
    const ativas = abas.findAll('.v8-abas-gatilho').map(t => t.attributes('data-state'))
    expect(ativas).toEqual(['inactive', 'active', 'inactive'])
  })

  it('V8-CMP-004: o flutuante vai para o body, na camada --z-popover', async () => {
    const css = ler(path.join(OFICIAL, 'primitivos.css'))
    const regra = /\.v8-dica,\s*\.v8-popover,\s*\.v8-suspenso,\s*\.v8-selecao\s*\{([^}]*)\}/.exec(css)
    expect(regra[1]).toMatch(/z-index:\s*var\(--z-popover\)/)

    const casca = montar(defineComponent({
      setup: () => () =>
        h('div', { id: 'casca' }, [
          h(Popover, { open: true, titulo: 'Filtros' }, {
            gatilho: () => h('button', { type: 'button' }, 'Abrir'),
            default: () => h('p', 'Conteúdo do popover')
          })
        ])
    }))
    await assentar()
    const conteudo = document.querySelector('.v8-popover')
    expect(conteudo).not.toBeNull()
    expect(casca.element.contains(conteudo)).toBe(false)
    expect(document.body.contains(conteudo)).toBe(true)
  })

  it('V8-CMP-004: dentro de um modal, ESC fecha só o flutuante', async () => {
    const aberto = ref(true)
    montar(defineComponent({
      setup: () => () =>
        h(DialogRoot, { open: true }, () =>
          h(DialogPortal, () =>
            h(DialogContent, { 'aria-describedby': undefined, class: 'modal-de-teste' }, () => [
              h(DialogTitle, () => 'Modal'),
              h(Popover, { open: aberto.value, 'onUpdate:open': v => (aberto.value = v), titulo: 'Dentro' }, {
                gatilho: () => h('button', { type: 'button' }, 'Abrir'),
                default: () => h('p', 'No popover')
              })
            ])
          )
        )
    }))
    await assentar()
    expect(document.querySelector('.v8-popover')).not.toBeNull()

    const alvo = document.activeElement || document.body
    alvo.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }))
    await assentar()
    await nextTick()

    expect(aberto.value).toBe(false)
    expect(document.querySelector('.modal-de-teste')).not.toBeNull()
  })

  it('V8-CMP-005: papéis ARIA e teclado das primitivas', async () => {
    const abas = montar(Abas, { props: { itens: OPCOES, rotulo: 'Bairros' } })
    expect(abas.find('[role="tablist"]').attributes('aria-label')).toBe('Bairros')
    expect(abas.findAll('[role="tab"]')).toHaveLength(3)
    expect(abas.find('[role="tabpanel"]').exists()).toBe(true)
    // O teclado é o do Reka UI: nenhum componente intercepta tecla nem muda tabindex.
    Object.keys(PRIMITIVAS).forEach(nome => {
      expect(fonte(nome), nome).not.toMatch(/@key(down|up|press)|onKey|tabindex/i)
    })

    const opcoes = montar(GrupoOpcoes, { props: { opcoes: OPCOES, rotulo: 'Bairro' } })
    expect(opcoes.find('[role="radiogroup"]').exists()).toBe(true)
    expect(opcoes.findAll('[role="radio"]')).toHaveLength(3)
    await opcoes.setProps({ modelValue: 'sul' })
    expect(opcoes.findAll('[role="radio"]').map(r => r.attributes('aria-checked'))).toEqual(['false', 'false', 'true'])

    const chave = montar(Chave, { props: { rotulo: 'Avisar' } })
    expect(chave.find('[role="switch"]').attributes('aria-checked')).toBe('false')
    const caixa = montar(CaixaMarcacao, { props: { rotulo: 'Aceito' } })
    expect(caixa.find('[role="checkbox"]').exists()).toBe(true)

    const selecao = montar(Selecao, { props: { opcoes: OPCOES, rotulo: 'Bairro' } })
    expect(selecao.find('[role="combobox"]').attributes('aria-label')).toBe('Bairro')

    montar(MenuSuspenso, { props: { open: true, itens: [{ valor: 'a', rotulo: 'A' }, { valor: 'b', rotulo: 'B' }] } })
    await assentar()
    expect(document.querySelector('[role="menu"]')).not.toBeNull()
    expect(document.querySelectorAll('[role="menuitem"]')).toHaveLength(2)

    const sanfona = montar(Sanfona, { props: { itens: [{ valor: 'a', titulo: 'Primeira' }], nivel: 'h4' } })
    const gatilho = sanfona.find('h4 button')
    expect(gatilho.attributes('aria-expanded')).toBe('false')
    await gatilho.trigger('click')
    expect(gatilho.attributes('aria-expanded')).toBe('true')

    montar(Dica, {
      props: { texto: 'Explicação curta' },
      slots: { default: () => h('button', { type: 'button', id: 'com-dica' }, 'Alvo') }
    })
    const alvo = document.getElementById('com-dica')
    expect(alvo).not.toBeNull()
  })

  it('V8-CMP-006: com name, dentro de um form, os valores vão no envio nativo', async () => {
    const Formulario = defineComponent({
      setup: () => () =>
        h('form', { id: 'form-de-teste' }, [
          h(CaixaMarcacao, { name: 'aceito', modelValue: true, rotulo: 'Aceito' }),
          h(Chave, { name: 'avisar', modelValue: true, rotulo: 'Avisar' }),
          h(GrupoOpcoes, { name: 'bairro', modelValue: 'norte', opcoes: OPCOES }),
          h(Selecao, { name: 'regiao', modelValue: 'sul', opcoes: OPCOES, rotulo: 'Região' })
        ])
    })
    montar(Formulario)
    await assentar()
    const dados = new FormData(document.getElementById('form-de-teste'))
    expect(dados.get('aceito')).toBe('on')
    expect(dados.get('avisar')).toBe('on')
    expect(dados.get('bairro')).toBe('norte')
    expect(dados.get('regiao')).toBe('sul')
  })

  it('V8-CMP-007: cor, raio, sombra, duração e camada vêm dos tokens', () => {
    const css = CSS_DOS_COMPONENTES.map(arquivo => ler(path.join(OFICIAL, arquivo))).join('\n')
    ;[...css.matchAll(/z-index:\s*([^;]+);/g)].forEach(m => expect(m[1].trim()).toBe('var(--z-popover)'))
    ;[...css.matchAll(/(?:transition|animation):\s*([^;]+);/g)].forEach(m => {
      expect(m[1], m[0]).toMatch(/var\(--duracao\)/)
    })
    Object.keys(PRIMITIVAS).forEach(nome => {
      const codigo = fonte(nome)
      // Geometria calculada (largura da barra, recuo por nível) pode ir em :style.
      expect(codigo, nome).not.toMatch(/\sstyle=|<style/)
      expect(codigo, nome).not.toMatch(/#[0-9a-fA-F]{3,8}\b|\brgba?\(/)
    })
  })

  it('V8-CMP-040: rótulos e textos são interpolados como texto', async () => {
    const hostil = '<img src=x onerror="alert(1)">'
    Object.keys(PRIMITIVAS).forEach(nome => expect(fonte(nome), nome).not.toMatch(/v-html|innerHTML/))
    const abas = montar(Abas, { props: { itens: [{ valor: 'a', rotulo: hostil }] } })
    expect(abas.find('img').exists()).toBe(false)
    expect(abas.text()).toContain(hostil)
    const chave = montar(Chave, { props: { rotulo: hostil } })
    expect(chave.find('img').exists()).toBe(false)
    montar(MenuSuspenso, { props: { open: true, itens: [{ valor: 'a', rotulo: hostil }] } })
    await assentar()
    expect(document.querySelector('.v8-suspenso img')).toBeNull()
  })

  it('V8-DS-014: a ilha ds-componentes mostra os nove componentes base', async () => {
    expect(Object.hasOwn(ilhas, 'ds-componentes')).toBe(true)
    const fetch = vi.fn()
    vi.stubGlobal('fetch', fetch)
    const ilha = montar(DsComponentes)
    await assentar()
    ;[Abas, Sanfona, Dica, Popover, MenuSuspenso, Selecao, CaixaMarcacao, GrupoOpcoes, Chave].forEach(componente => {
      expect(ilha.findComponent(componente).exists(), componente.__name).toBe(true)
    })
    expect(ilha.findAll('[role="tab"]').length).toBeGreaterThan(0)
    expect(ilha.findAll('[role="switch"]').length).toBe(3)
    expect(fetch).not.toHaveBeenCalled()
    vi.unstubAllGlobals()
  })
})
