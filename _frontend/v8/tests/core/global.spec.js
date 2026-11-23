import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

import { ID_DADOS_GLOBAIS, dadosPadrao, useGlobalStore } from '~@/stores/GlobalStore'

function escreverGlobal(texto) {
  const el = document.createElement('script')
  el.id = ID_DADOS_GLOBAIS
  el.type = 'application/json'
  el.textContent = texto
  document.body.appendChild(el)
  return el
}

function esperarAnonimo(store) {
  const padrao = dadosPadrao()
  expect(store.autenticado).toBe(false)
  expect(store.usuario).toBeNull()
  expect(store.permissoes).toEqual([])
  expect(store.urls).toEqual(padrao.urls)
  expect(store.sidebar).toBe('expandida')
  expect(store.tema).toBe('oficial')
  expect(store.modo).toBeNull()
  expect(store.carregado).toBe(true)
}

describe('GlobalStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('V8-TEMA-021, V8-ARQ-032: carregar() preenche o store com o JSON de #v8-global', () => {
    escreverGlobal(JSON.stringify({
      versao: 'v8.1',
      autenticado: true,
      usuario: { id: 7, nome: 'Fulana' },
      permissoes: ['materia.add_materialegislativa'],
      urls: { login: '/entrar/' },
      zonas: { demo: '/v8/demo/' },
      zona: 'demo',
      tema: 'terracota',
      modo: 'escuro',
      sidebar: 'recolhida'
    }))
    const store = useGlobalStore()

    store.carregar()

    expect(store.carregado).toBe(true)
    expect(store.versao).toBe('v8.1')
    expect(store.autenticado).toBe(true)
    expect(store.usuario).toEqual({ id: 7, nome: 'Fulana' })
    expect(store.permissoes).toEqual(['materia.add_materialegislativa'])
    expect(store.tema).toBe('terracota')
    expect(store.modo).toBe('escuro')
    expect(store.sidebar).toBe('recolhida')
    expect(store.prefixoZona).toBe('/v8/demo/')
    // As URLs que o servidor não informou continuam com o padrão.
    expect(store.urls.login).toBe('/entrar/')
    expect(store.urls.api).toBe(dadosPadrao().urls.api)
  })

  it('V8-ARQ-032: sem #v8-global o usuário é anônimo e não há exceção', () => {
    const store = useGlobalStore()

    expect(() => store.carregar()).not.toThrow()

    esperarAnonimo(store)
  })

  it.each([
    ['JSON truncado', '{"autenticado": true, "usuario": '],
    ['texto que não é JSON', 'autenticado = true'],
    ['script vazio', ''],
    ['lista no lugar do objeto', '[{"autenticado": true}]'],
    ['null', 'null'],
    ['texto solto', '"autenticado"']
  ])('V8-ARQ-032: JSON inválido (%s) resulta em usuário anônimo, sem exceção', (_caso, texto) => {
    escreverGlobal(texto)
    const store = useGlobalStore()

    expect(() => store.carregar()).not.toThrow()

    esperarAnonimo(store)
  })

  it('V8-ARQ-032: a segunda chamada de carregar() não relê o documento', () => {
    const el = escreverGlobal(JSON.stringify({ versao: 'primeira', autenticado: true }))
    const store = useGlobalStore()
    const leitura = vi.spyOn(document, 'getElementById')

    store.carregar()
    expect(leitura).toHaveBeenCalledTimes(1)

    el.textContent = JSON.stringify({ versao: 'segunda', autenticado: false })
    store.carregar()

    expect(leitura).toHaveBeenCalledTimes(1)
    expect(store.versao).toBe('primeira')
    expect(store.autenticado).toBe(true)
  })

  it('V8-ARQ-062: valor com </script>, aspas e & chega ao store idêntico', () => {
    const perigoso = '</script><script>alert(1)</script>"\'&'
    escreverGlobal(JSON.stringify({
      versao: perigoso,
      usuario: { nome: perigoso },
      flags: { [perigoso]: perigoso }
    }))
    const store = useGlobalStore()

    store.carregar()

    expect(store.versao).toBe(perigoso)
    expect(store.usuario.nome).toBe(perigoso)
    expect(store.flags[perigoso]).toBe(perigoso)
    // O valor não criou nenhum script além do próprio json_script.
    expect(document.querySelectorAll('script')).toHaveLength(1)
  })

  it('V8-ARQ-062: o escape do json_script do Django é desfeito na leitura', () => {
    const perigoso = '</script><script>alert(1)</script>"\'&'
    // O json_script troca <, > e & por <, > e &.
    const escapado = JSON.stringify({ versao: perigoso })
      .replace(/</g, '\\u003C')
      .replace(/>/g, '\\u003E')
      .replace(/&/g, '\\u0026')
    document.body.innerHTML =
      `<script id="${ID_DADOS_GLOBAIS}" type="application/json">${escapado}</script>`
    const store = useGlobalStore()

    store.carregar()

    expect(store.versao).toBe(perigoso)
    expect(document.querySelectorAll('script')).toHaveLength(1)
  })
})
