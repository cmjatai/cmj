import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { ilhas } from '~@/core/ilhas'
import ClientesTabela from '~@/modules/demo/ilhas/ClientesTabela.vue'
import { paginaDeExemplo } from './apoio'

const clientes = [
  ...paginaDeExemplo().itens,
  { id: 9, nome: 'Bento Modelo', email: 'bento.modelo@exemplo.invalid', cidade: 'Mineiros', situacao: 'ativo' }
]

function montar(props = {}) {
  // O formulário da ação em massa é desenhado pelo Django, fora da ilha.
  const formulario = document.createElement('form')
  formulario.id = 'demo-arquivar'
  document.body.appendChild(formulario)
  const wrapper = mount(ClientesTabela, {
    props: { clientes, formulario: 'demo-arquivar', ...props },
    attachTo: document.body
  })
  return {
    wrapper,
    formulario,
    todos: () => wrapper.find('thead input[type="checkbox"]'),
    linhas: () => wrapper.findAll('tbody input[type="checkbox"]'),
    contagem: () => wrapper.find('[aria-live="polite"]').text()
  }
}

describe('ilha demo-clientes-tabela', () => {
  it('V8-DEMO-011: o registro de ilhas carrega este componente', async () => {
    const modulo = await ilhas['demo-clientes-tabela']()
    expect(modulo.default).toBe(ClientesTabela)
  })

  it('V8-DEMO-011: desenha uma linha por cliente, com a etiqueta da situação', () => {
    const { wrapper } = montar()
    const linhas = wrapper.findAll('tbody tr')
    expect(linhas).toHaveLength(3)
    expect(linhas[0].text()).toContain('Ana Exemplo')
    expect(linhas[0].text()).toContain('ana.exemplo@exemplo.invalid')
    expect(linhas[0].text()).toContain('Caiapônia')
    expect(linhas[0].find('.v8-etiqueta-ok').text()).toBe('Ativo')
    expect(linhas[1].find('.v8-etiqueta-neutra').text()).toBe('Inativo')
    wrapper.unmount()
  })

  it('V8-DEMO-011: cada caixa de seleção pertence ao formulário da ação em massa', async () => {
    const { wrapper, formulario, linhas } = montar()
    linhas().forEach((caixa, i) => {
      expect(caixa.attributes('name')).toBe('ids')
      expect(caixa.attributes('form')).toBe('demo-arquivar')
      expect(caixa.attributes('value')).toBe(String(clientes[i].id))
      expect(caixa.attributes('aria-label')).toBe(`Selecionar ${clientes[i].nome}`)
    })
    await linhas()[0].setValue(true)
    await linhas()[2].setValue(true)
    // São os ids marcados que o formulário do servidor envia.
    expect(new FormData(formulario).getAll('ids')).toEqual(['1', '9'])
    wrapper.unmount()
  })

  it('V8-DEMO-011: "selecionar todos" não entra no envio do formulário', () => {
    const { wrapper, todos } = montar()
    expect(todos().attributes('aria-label')).toBe('Selecionar todos')
    expect(todos().attributes('name')).toBeUndefined()
    expect(todos().attributes('form')).toBeUndefined()
    wrapper.unmount()
  })

  it('V8-DEMO-011: a contagem acompanha a seleção de linhas', async () => {
    const { wrapper, linhas, contagem } = montar()
    expect(contagem()).toBe('0 selecionados')
    await linhas()[1].setValue(true)
    expect(contagem()).toBe('1 selecionado')
    await linhas()[2].setValue(true)
    expect(contagem()).toBe('2 selecionados')
    await linhas()[1].setValue(false)
    expect(contagem()).toBe('1 selecionado')
    wrapper.unmount()
  })

  it('V8-DEMO-011: "selecionar todos" marca e desmarca todas as linhas', async () => {
    const { wrapper, formulario, todos, linhas, contagem } = montar()
    await todos().setValue(true)
    expect(linhas().every(caixa => caixa.element.checked)).toBe(true)
    expect(contagem()).toBe('3 selecionados')
    expect(new FormData(formulario).getAll('ids')).toEqual(['1', '4', '9'])
    await todos().setValue(false)
    expect(linhas().some(caixa => caixa.element.checked)).toBe(false)
    expect(contagem()).toBe('0 selecionados')
    wrapper.unmount()
  })

  it('V8-DEMO-011: "selecionar todos" fica indeterminado com seleção parcial', async () => {
    const { wrapper, todos, linhas } = montar()
    expect(todos().element.indeterminate).toBe(false)
    await linhas()[0].setValue(true)
    expect(todos().element.indeterminate).toBe(true)
    expect(todos().element.checked).toBe(false)
    await linhas()[1].setValue(true)
    await linhas()[2].setValue(true)
    expect(todos().element.indeterminate).toBe(false)
    expect(todos().element.checked).toBe(true)
    wrapper.unmount()
  })

  it('V8-DEMO-011: sem clientes, mostra a linha de lista vazia e desliga "selecionar todos"', () => {
    const { wrapper, todos, linhas } = montar({ clientes: [] })
    expect(linhas()).toHaveLength(0)
    expect(wrapper.find('tbody').text()).toContain('Nenhum cliente encontrado')
    expect(todos().element.disabled).toBe(true)
    expect(todos().element.checked).toBe(false)
    wrapper.unmount()
  })

  it('V8-DEMO-013: o nome é um link para o detalhe, com o gatilho do drawer direito', () => {
    const { wrapper } = montar()
    const links = wrapper.findAll('tbody a')
    expect(links).toHaveLength(3)
    expect(links[1].text()).toBe('Davi Exemplo')
    expect(links[1].attributes('href')).toBe('/v8/demo/clientes/4/')
    expect(links[1].attributes('data-drawer')).toBe('cliente:4')
    expect(links[1].attributes('data-drawer-side')).toBe('right')
    wrapper.unmount()
  })
})
