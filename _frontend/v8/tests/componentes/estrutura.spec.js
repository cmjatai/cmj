// Componentes de navegação e estrutura (docs/specs/v8/componentes.md).
import path from 'path'
import { afterEach, describe, expect, it } from 'vitest'
import { nextTick } from 'vue'
import AreaRolagem from '~@/componentes/AreaRolagem.vue'
import Arvore from '~@/componentes/Arvore.vue'
import Avatar from '~@/componentes/Avatar.vue'
import BarraFerramentas from '~@/componentes/BarraFerramentas.vue'
import BarraMenus from '~@/componentes/BarraMenus.vue'
import CartaoFlutuante from '~@/componentes/CartaoFlutuante.vue'
import Divisor from '~@/componentes/Divisor.vue'
import Etapas from '~@/componentes/Etapas.vue'
import MenuContexto from '~@/componentes/MenuContexto.vue'
import MenuNavegacao from '~@/componentes/MenuNavegacao.vue'
import Paginacao from '~@/componentes/Paginacao.vue'
import Progresso from '~@/componentes/Progresso.vue'
import Proporcao from '~@/componentes/Proporcao.vue'
import Recolhivel from '~@/componentes/Recolhivel.vue'
import Separador from '~@/componentes/Separador.vue'
import { ilhas } from '~@/core/ilhas'
import DsEstrutura from '~@/modules/ds/ilhas/DsEstrutura.vue'
import { assentar } from '../demo/apoio'
import { OFICIAL, desmontarTodos, ler, montar } from './apoio'

const ITENS = [
  { valor: 'copiar', rotulo: 'Copiar' },
  { separador: true },
  { valor: 'excluir', rotulo: 'Excluir', perigo: true }
]

describe('componentes de navegação e estrutura', () => {
  afterEach(desmontarTodos)

  it('V8-CMP-020: recolhível, barras, menus e cartão sobre as primitivas do Reka UI', async () => {
    const recolhivel = montar(Recolhivel, { props: { titulo: 'Detalhes' }, slots: { default: 'Conteúdo' } })
    expect(recolhivel.text()).not.toContain('Conteúdo')
    await recolhivel.find('button').trigger('click')
    await assentar()
    expect(recolhivel.emitted('update:open')).toEqual([[true]])
    expect(recolhivel.text()).toContain('Conteúdo')

    const ferramentas = montar(BarraFerramentas, {
      props: {
        rotulo: 'Formatação',
        itens: [{ valor: 'salvar', rotulo: 'Salvar' }],
        alternadores: [{ valor: 'negrito', rotulo: 'N' }],
        multiplo: true,
        modelValue: []
      }
    })
    expect(ferramentas.find('[role="toolbar"]').attributes('aria-label')).toBe('Formatação')
    await ferramentas.findAll('button')[0].trigger('click')
    expect(ferramentas.emitted('acionar')).toEqual([['salvar']])
    await ferramentas.find('[aria-pressed]').trigger('click')
    expect(ferramentas.emitted('update:modelValue')).toEqual([[['negrito']]])

    const barra = montar(BarraMenus, {
      props: { modelValue: 'arquivo', menus: [{ valor: 'arquivo', rotulo: 'Arquivo', itens: ITENS }] }
    })
    await assentar()
    expect(barra.find('[role="menubar"]').exists()).toBe(true)
    const menu = document.querySelector('.v8-suspenso[role="menu"]')
    expect(menu).not.toBeNull()
    expect(barra.element.contains(menu)).toBe(false)
    menu.querySelector('[role="menuitem"]').click()
    await assentar()
    expect(barra.emitted('selecionar')).toEqual([['copiar']])
  })

  it('V8-CMP-020: o menu de contexto abre com o botão direito, fora da página', async () => {
    const contexto = montar(MenuContexto, { props: { itens: ITENS }, slots: { default: '<p>Alvo</p>' } })
    contexto.find('.v8-menu-contexto-alvo').element.dispatchEvent(
      new MouseEvent('contextmenu', { bubbles: true, cancelable: true, clientX: 10, clientY: 10 })
    )
    await nextTick()
    await assentar()
    const menu = document.querySelector('.v8-suspenso[role="menu"]')
    expect(menu).not.toBeNull()
    expect(contexto.element.contains(menu)).toBe(false)
    expect([...menu.querySelectorAll('[role="menuitem"]')].map(i => i.textContent.trim())).toEqual(['Copiar', 'Excluir'])
  })

  it('V8-CMP-020: o conteúdo flutuante usa a camada --z-popover', async () => {
    const css = ler(path.join(OFICIAL, 'estrutura.css'))
    ;['v8-cartao-flutuante', 'v8-menu-navegacao-painel'].forEach(classe => {
      const regra = new RegExp(`\\.${classe}\\s*\\{([^}]*)\\}`).exec(css)
      expect(regra[1], classe).toMatch(/z-index:\s*var\(--z-popover\)/)
    })

    const cartao = montar(CartaoFlutuante, {
      props: { open: true },
      slots: { gatilho: '<a href="#x">Pessoa</a>', default: '<p>Prévia</p>' }
    })
    await assentar()
    const conteudo = document.querySelector('.v8-cartao-flutuante')
    expect(conteudo?.textContent).toContain('Prévia')
    expect(cartao.element.contains?.(conteudo)).not.toBe(true)

    const navegacao = montar(MenuNavegacao, {
      props: {
        rotulo: 'Seções',
        modelValue: 'temas',
        itens: [
          { valor: 'inicio', rotulo: 'Início', href: '/v8/', ativo: true },
          { valor: 'temas', rotulo: 'Temas', links: [{ rotulo: 'Lista', href: '/v8/ds/temas/' }] }
        ]
      }
    })
    await assentar()
    expect(navegacao.find('nav').attributes('aria-label')).toBe('Seções')
    expect(navegacao.find('a[aria-current="page"]').text()).toBe('Início')
    expect(navegacao.find('.v8-menu-navegacao-painel').text()).toContain('Lista')
  })

  it('V8-CMP-020: paginação, etapas, árvore, divisor e área de rolagem', async () => {
    const paginacao = montar(Paginacao, { props: { total: 240, porPagina: 20, page: 3 } })
    const atual = paginacao.find('[aria-current="page"]')
    expect(atual.text()).toBe('3')
    expect(paginacao.find('nav').attributes('aria-label')).toBe('Paginação')
    await paginacao.find('[aria-label="Próxima página"]').trigger('click')
    expect(paginacao.emitted('update:page')).toEqual([[4]])
    expect(paginacao.text()).toContain('12')

    const etapas = montar(Etapas, {
      props: { modelValue: 2, passos: [{ titulo: 'Protocolo' }, { titulo: 'Comissão' }, { titulo: 'Plenário' }] }
    })
    expect(etapas.find('[role="group"]').attributes('aria-label')).toBe('Etapas')
    expect(etapas.findAll('.v8-etapas-item').map(i => i.attributes('data-state'))).toEqual([
      'completed',
      'active',
      'inactive'
    ])

    const arvore = montar(Arvore, {
      props: {
        rotulo: 'Pastas',
        expanded: ['documentos'],
        itens: [
          { valor: 'documentos', rotulo: 'Documentos', filhos: [{ valor: 'atas', rotulo: 'Atas' }] },
          { valor: 'imagens', rotulo: 'Imagens' }
        ]
      }
    })
    expect(arvore.find('[role="tree"]').attributes('aria-label')).toBe('Pastas')
    expect(arvore.findAll('[role="treeitem"]').map(i => i.text())).toEqual(['Documentos', 'Atas', 'Imagens'])
    expect(arvore.findAll('[role="treeitem"]').map(i => i.attributes('aria-level'))).toEqual(['1', '2', '1'])

    const divisor = montar(Divisor, { slots: { primeiro: 'A', segundo: 'B' } })
    expect(divisor.find('[role="separator"]').attributes('aria-label')).toBe('Redimensionar painéis')
    expect(divisor.findAll('[data-panel]')).toHaveLength(2)

    const rolagem = montar(AreaRolagem, { props: { rotulo: 'Itens' }, slots: { default: '<p>Item</p>' } })
    expect(rolagem.find('[data-reka-scroll-area-viewport]').exists()).toBe(true)
    expect(rolagem.text()).toContain('Item')
  })

  it('V8-CMP-020: separador, avatar, progresso e proporção', async () => {
    expect(montar(Separador).find('[role="separator"]').exists()).toBe(true)
    expect(montar(Separador, { props: { decorativo: true } }).find('[role="none"]').exists()).toBe(true)

    const avatar = montar(Avatar, { props: { nome: 'Ana Maria Lima' } })
    await assentar()
    expect(avatar.text()).toBe('AL')
    expect(montar(Avatar, { props: { nome: '' } }).text()).toBe('?')

    const progresso = montar(Progresso, { props: { modelValue: 60, rotulo: 'Envio' } })
    const barra = progresso.find('[role="progressbar"]')
    expect(barra.attributes('aria-valuenow')).toBe('60')
    expect(barra.attributes('aria-label')).toBe('Envio: 60%')
    const indeterminado = montar(Progresso)
    expect(indeterminado.find('[role="progressbar"]').attributes('data-state')).toBe('indeterminate')

    const proporcao = montar(Proporcao, { slots: { default: 'x' } })
    expect(proporcao.find('[data-reka-aspect-ratio-wrapper]').exists()).toBe(true)
  })

  it('V8-DS-016: a ilha ds-estrutura mostra os componentes de navegação e estrutura', async () => {
    expect(Object.hasOwn(ilhas, 'ds-estrutura')).toBe(true)
    const ilha = montar(DsEstrutura)
    await assentar()
    ;[Recolhivel, BarraFerramentas, BarraMenus, MenuContexto, MenuNavegacao, CartaoFlutuante, Paginacao, Etapas,
      Arvore, Divisor, AreaRolagem, Separador, Avatar, Progresso, Proporcao].forEach(componente => {
      expect(ilha.findComponent(componente).exists(), componente.__name).toBe(true)
    })
  })
})
