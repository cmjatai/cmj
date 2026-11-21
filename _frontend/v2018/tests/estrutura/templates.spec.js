// Regra conferida lendo os templates Django: o que pode existir dentro do elemento em que o
// Vue é montado (`#app` na entrada app, `#app-vue` na entrada construct).
import fs from 'fs'
import path from 'path'
import { describe, expect, it } from 'vitest'

const TEMPLATES = path.resolve(__dirname, '../../../../_templates')

function arquivos (pasta) {
  return fs.readdirSync(pasta, { withFileTypes: true }).flatMap(item => {
    const caminho = path.join(pasta, item.name)
    if (item.isDirectory()) {
      return arquivos(caminho)
    }
    return item.name.endsWith('.html') ? [caminho] : []
  })
}

// Conteúdo de cada `<div id="app">` ou `<div id="app-vue">`, até o `</div>` que o fecha.
function montagens (texto) {
  const achadas = []
  const abertura = /<div id="app(?:-vue)?">/g
  let m
  while ((m = abertura.exec(texto)) !== null) {
    const inicio = m.index + m[0].length
    const tags = /<div\b|<\/div>/g
    tags.lastIndex = inicio
    let nivel = 1
    let t
    while (nivel > 0 && (t = tags.exec(texto)) !== null) {
      nivel += t[0] === '</div>' ? -1 : 1
    }
    achadas.push(texto.slice(inicio, t ? t.index : texto.length))
  }
  return achadas
}

// Única variável aceita: um id numérico como valor de atributo, como `:classe_id="{{object.id}}"`.
const ID_EM_ATRIBUTO = /="\{\{\s*[\w.]+\.(?:id|pk)\s*\}\}"/g

describe('HTML do Django dentro do elemento montado pelo Vue', () => {
  const casos = arquivos(TEMPLATES).flatMap(caminho => {
    const texto = fs.readFileSync(caminho, 'utf8')
    return montagens(texto).map(conteudo => [path.relative(TEMPLATES, caminho), conteudo])
  })

  it('V2018-EST-043: os templates com elemento de montagem são encontrados', () => {
    expect(casos.length).toBeGreaterThanOrEqual(5)
  })

  it.each(casos)('V2018-EST-043: %s só tem tags de componente e id numérico em atributo', (arquivo, conteudo) => {
    const semIds = conteudo.replace(ID_EM_ATRIBUTO, '=""')
    expect(semIds).not.toMatch(/\{\{/)
    expect(semIds).not.toMatch(/\{%/)
    expect(semIds).not.toMatch(/\[\[/)
    expect(semIds.replace(/<[^>]*>/g, '').trim()).toBe('')
  })
})
