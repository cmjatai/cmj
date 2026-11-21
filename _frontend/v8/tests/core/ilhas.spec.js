import { afterEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { defineComponent, h, onUnmounted } from 'vue'
import IslandHost from '~@/core/IslandHost.vue'

let host

async function assentar() {
  for (let i = 0; i < 3; i += 1) {
    await flushPromises()
    await new Promise(resolver => setTimeout(resolver, 0))
  }
}

function ilhaDeTeste(estado = {}) {
  return defineComponent({
    props: { nome: { type: String, default: '' }, itens: { type: Array, default: () => [] } },
    setup(props) {
      estado.montagens = (estado.montagens || 0) + 1
      onUnmounted(() => (estado.desmontagens = (estado.desmontagens || 0) + 1))
      return () => h('p', { 'data-ilha-viva': '' }, `${props.nome}:${props.itens.length}`)
    }
  })
}

function montarHost(registro) {
  host = mount(IslandHost, { props: { registro }, attachTo: document.body })
  return host
}

afterEach(() => host?.unmount())

describe('ilhas', () => {
  it('V8-ARQ-033: monta o componente registrado, com as props do json_script', async () => {
    document.body.innerHTML = `
      <script id="p1" type="application/json">{"nome": "clientes", "itens": [1, 2, 3]}</script>
      <div data-vue-island="tabela" data-props-id="p1"><table><tr><td>do servidor</td></tr></table></div>`
    const carregar = vi.fn(() => Promise.resolve({ default: ilhaDeTeste() }))
    montarHost({ tabela: carregar })
    await assentar()
    const el = document.querySelector('[data-vue-island]')
    expect(el.querySelector('[data-ilha-viva]').textContent).toBe('clientes:3')
    expect(el.querySelector('table')).toBeNull()
    expect(carregar).toHaveBeenCalledTimes(1)
  })

  it('V8-ARQ-033: o código de uma ilha só é pedido em página que a contém', async () => {
    document.body.innerHTML = '<div data-vue-island="tabela"></div>'
    const tabela = vi.fn(() => Promise.resolve({ default: ilhaDeTeste() }))
    const grafico = vi.fn(() => Promise.resolve({ default: ilhaDeTeste() }))
    montarHost({ tabela, grafico })
    await assentar()
    expect(tabela).toHaveBeenCalledTimes(1)
    expect(grafico).not.toHaveBeenCalled()
  })

  it('V8-ARQ-034: o HTML do servidor fica até o componente estar pronto', async () => {
    document.body.innerHTML = '<div data-vue-island="tabela"><p data-servidor>do servidor</p></div>'
    let liberar
    montarHost({ tabela: () => new Promise(ok => (liberar = ok)) })
    await assentar()
    expect(document.querySelector('[data-servidor]')).not.toBeNull()
    liberar({ default: ilhaDeTeste() })
    await assentar()
    expect(document.querySelector('[data-servidor]')).toBeNull()
    expect(document.querySelector('[data-ilha-viva]')).not.toBeNull()
  })

  it('V8-ARQ-034: nome desconhecido ou falha ao baixar mantêm o HTML e não afetam as outras', async () => {
    vi.spyOn(console, 'warn').mockImplementation(() => {})
    vi.spyOn(console, 'error').mockImplementation(() => {})
    document.body.innerHTML = `
      <div data-vue-island="nao-existe"><p data-a>a</p></div>
      <div data-vue-island="quebrada"><p data-b>b</p></div>
      <div data-vue-island="boa"><p data-c>c</p></div>`
    montarHost({
      quebrada: () => Promise.reject(new Error('rede')),
      boa: () => Promise.resolve({ default: ilhaDeTeste() })
    })
    await assentar()
    expect(document.querySelector('[data-a]')).not.toBeNull()
    expect(document.querySelector('[data-b]')).not.toBeNull()
    expect(document.querySelector('[data-c]')).toBeNull()
    expect(document.querySelectorAll('[data-ilha-viva]')).toHaveLength(1)
  })

  it('V8-ARQ-064: o nome da ilha só é resolvido pelo registro', async () => {
    vi.spyOn(console, 'warn').mockImplementation(() => {})
    document.body.innerHTML = `
      <div data-vue-island="constructor"><p data-a>a</p></div>
      <div data-vue-island="../../segredo"><p data-b>b</p></div>
      <div data-vue-island="https://exemplo.invalid/x.js"><p data-c>c</p></div>`
    montarHost({})
    await assentar()
    expect(document.querySelectorAll('[data-ilha-viva]')).toHaveLength(0)
    expect(document.querySelectorAll('[data-a], [data-b], [data-c]')).toHaveLength(3)
  })

  it('V8-ARQ-035: ilha em HTML inserido depois é montada ao entrar e desmontada ao sair', async () => {
    document.body.innerHTML = '<div id="drawer"></div>'
    const estado = {}
    montarHost({ tabela: () => Promise.resolve({ default: ilhaDeTeste(estado) }) })
    await assentar()
    expect(estado.montagens).toBeUndefined()

    document.getElementById('drawer').innerHTML = '<section><div data-vue-island="tabela"></div></section>'
    await assentar()
    expect(estado.montagens).toBe(1)
    expect(document.querySelector('#drawer [data-ilha-viva]')).not.toBeNull()

    document.getElementById('drawer').innerHTML = ''
    await assentar()
    expect(estado.desmontagens).toBe(1)
  })

  it('V8-ARQ-063: texto do servidor com {{ }} ou [[ ]] fica literal', async () => {
    document.body.innerHTML = `
      <main id="conteudo"><p id="t">{{ 7 * 7 }} [[ 7 * 7 ]] <span v-html="'x'">v</span></p></main>
      <div data-vue-island="tabela"></div>`
    montarHost({ tabela: () => Promise.resolve({ default: ilhaDeTeste() }) })
    await assentar()
    expect(document.getElementById('t').textContent).toBe('{{ 7 * 7 }} [[ 7 * 7 ]] v')
  })

  it('V8-ARQ-062: props com marcação chegam ao componente idênticas', async () => {
    const hostil = '</script><script>alert(1)</script>"\'&'
    document.body.innerHTML = '<script id="p1" type="application/json"></script><div data-vue-island="tabela" data-props-id="p1"></div>'
    document.getElementById('p1').textContent = JSON.stringify({ nome: hostil, itens: [] })
    montarHost({ tabela: () => Promise.resolve({ default: ilhaDeTeste() }) })
    await assentar()
    expect(document.querySelector('[data-ilha-viva]').textContent).toBe(`${hostil}:0`)
    expect(document.querySelectorAll('script:not([type])')).toHaveLength(0)
  })
})
