import { readFileSync, readdirSync } from 'node:fs'
import path from 'node:path'

import { describe, expect, it } from 'vitest'

// Varredura do código-fonte: regras que valem para o v8 inteiro, não para um módulo.
const RAIZ = path.resolve('src')
const CLIENTE = 'http/client.js'

function arquivos(pasta) {
  return readdirSync(pasta, { withFileTypes: true }).flatMap(item => {
    const caminho = path.join(pasta, item.name)
    if (item.isDirectory()) {
      return arquivos(caminho)
    }
    return /\.(js|vue)$/.test(item.name) ? [caminho] : []
  })
}

function relativo(caminho) {
  return path.relative(RAIZ, caminho).split(path.sep).join('/')
}

// Tira os comentários, que podem citar fetch e axios à vontade.
function semComentarios(texto) {
  return texto
    .replace(/\/\*[\s\S]*?\*\//g, '')
    .replace(/<!--[\s\S]*?-->/g, '')
    .replace(/^\s*\/\/.*$/gm, '')
    .replace(/\s\/\/\s.*$/gm, '')
}

// Chamada a método de objeto, como Resources.Utils.fetch(...) e store.fetchSync(...), é permitida.
const PROIBIDOS = [
  { nome: 'fetch(', padrao: /(?<![\w.$])fetch\s*\(/ },
  { nome: 'window.fetch', padrao: /\b(?:window|globalThis|self)\s*\.\s*fetch\b/ },
  { nome: 'XMLHttpRequest', padrao: /new\s+XMLHttpRequest\b|\bXMLHttpRequest\s*\(/ },
  { nome: 'axios', padrao: /from\s+['"]axios['"]|(?:require|import)\s*\(\s*['"]axios['"]\s*\)|\baxios\s*[.(]/ }
]

function ocorrencias(texto) {
  const limpo = semComentarios(texto)
  return PROIBIDOS.filter(p => p.padrao.test(limpo)).map(p => p.nome)
}

describe('varredura do código-fonte', () => {
  it('V8-HTTP-001: a varredura reconhece o que é proibido e o que é permitido', () => {
    expect(ocorrencias('const r = await fetch(url)')).toEqual(['fetch('])
    expect(ocorrencias('window.fetch(url)')).toEqual(['window.fetch'])
    expect(ocorrencias('const f = globalThis.fetch')).toEqual(['window.fetch'])
    expect(ocorrencias('const x = new XMLHttpRequest()')).toEqual(['XMLHttpRequest'])
    expect(ocorrencias('import axios from \'axios\'')).toEqual(['axios'])
    expect(ocorrencias('axios.get(url)')).toEqual(['axios'])
    expect(ocorrencias('Resources.Utils.fetch({ app, model })')).toEqual([])
    expect(ocorrencias('const _fetch = Resources.Utils.fetch\n_fetch(metadata)')).toEqual([])
    expect(ocorrencias('store.fetchSync({ app })\nfetch: (m) => m')).toEqual([])
    expect(ocorrencias('// antes era fetch(url) com axios.get\nconst a = 1 // fetch(x)')).toEqual([])
  })

  it('V8-HTTP-001: só src/http/client.js chama fetch, XMLHttpRequest ou axios', () => {
    const todos = arquivos(RAIZ)
    expect(todos.map(relativo)).toContain(CLIENTE)
    const achados = todos
      .filter(caminho => relativo(caminho) !== CLIENTE)
      .flatMap(caminho => ocorrencias(readFileSync(caminho, 'utf8')).map(nome => `${relativo(caminho)}: ${nome}`))
    expect(achados).toEqual([])
  })

  it('V8-HTTP-001: o cliente é o único caminho e não usa XMLHttpRequest nem axios', () => {
    const texto = readFileSync(path.join(RAIZ, CLIENTE), 'utf8')
    expect(ocorrencias(texto)).toEqual(['fetch('])
  })

  it('V8-HTTP-043: os fontes de src/http não mencionam campo de senha', () => {
    const fontes = arquivos(path.join(RAIZ, 'http'))
    expect(fontes.length).toBeGreaterThanOrEqual(4)
    fontes.forEach(caminho => {
      const texto = readFileSync(caminho, 'utf8')
      expect(texto, relativo(caminho)).not.toMatch(/password|passwd|senha/i)
    })
  })

  it('V8-HTTP-043: Resources.Utils e AuthStore não têm mais login por senha', () => {
    const resources = readFileSync(path.join(RAIZ, 'utils/resources/index.js'), 'utf8')
    const auth = readFileSync(path.join(RAIZ, 'stores/AuthStore.js'), 'utf8')
    ;[resources, auth].forEach(texto => {
      expect(texto).not.toMatch(/password|passwd|senha|loginPortalCMJ/i)
    })
  })
})
