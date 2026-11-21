// Regras conferidas lendo os arquivos: entradas do webpack e bundles pedidos pelos templates.
// O vue.config.js é lido como texto, sem ser executado, porque ele carrega o .env do backend.
import fs from 'fs'
import path from 'path'
import { describe, expect, it } from 'vitest'

const RAIZ = path.resolve(__dirname, '../..')
const TEMPLATES = path.resolve(RAIZ, '../../_templates')
const vueConfig = fs.readFileSync(path.join(RAIZ, 'vue.config.js'), 'utf8')

function entradasDeclaradas () {
  const entradas = {}
  const expressao = /config\.entry\('([^']+)'\)\s*\.add\('([^']+)'\)/g
  let m
  while ((m = expressao.exec(vueConfig)) !== null) {
    entradas[m[1]] = m[2]
  }
  return entradas
}

function arquivos (pasta, extensao) {
  const achados = []
  fs.readdirSync(pasta, { withFileTypes: true }).forEach(item => {
    const caminho = path.join(pasta, item.name)
    if (item.isDirectory()) {
      achados.push(...arquivos(caminho, extensao))
    } else if (item.name.endsWith(extensao)) {
      achados.push(caminho)
    }
  })
  return achados
}

// Nomes literais em `{% render_bundle 'nome' ... %}`; o nome vindo de variável fica de fora.
function bundlesPedidos () {
  const pedidos = {}
  arquivos(TEMPLATES, '.html').forEach(caminho => {
    const expressao = /\{%\s*render_bundle\s+'([^']+)'/g
    const texto = fs.readFileSync(caminho, 'utf8')
    let m
    while ((m = expressao.exec(texto)) !== null) {
      pedidos[m[1]] = pedidos[m[1]] || []
      pedidos[m[1]].push(path.relative(TEMPLATES, caminho))
    }
  })
  return pedidos
}

describe('entradas do webpack', () => {
  const entradas = entradasDeclaradas()

  it('V2018-EST-002: as entradas extras são construct, compilacao, loa e libsuserauth', () => {
    expect(Object.keys(entradas).sort()).toEqual(['compilacao', 'construct', 'libsuserauth', 'loa'])
  })

  it('V2018-EST-002: o arquivo de cada entrada existe, inclusive o da entrada app', () => {
    const caminhos = ['./src/main.js', ...Object.values(entradas)]
    const ausentes = caminhos.filter(c => !fs.existsSync(path.join(RAIZ, c)))
    expect(ausentes).toEqual([])
  })

  it('V2018-EST-002: toda pasta de src/__apps com main.js é entrada', () => {
    const pastas = fs.readdirSync(path.join(RAIZ, 'src/__apps'), { withFileTypes: true })
      .filter(item => item.isDirectory())
      .filter(item => fs.existsSync(path.join(RAIZ, 'src/__apps', item.name, 'main.js')))
      .map(item => item.name)
    const semEntrada = pastas.filter(nome => entradas[nome] !== `./src/__apps/${nome}/main.js`)
    expect(semEntrada).toEqual([])
  })

  it('V2018-EST-004: o webpack fornece $, jQuery, window.jQuery e _ sem import', () => {
    const bloco = /ProvidePlugin, \[\{([\s\S]*?)\}\]/.exec(vueConfig)[1]
    expect(bloco).toMatch(/\$: 'jquery'/)
    expect(bloco).toMatch(/jQuery: 'jquery'/)
    expect(bloco).toMatch(/'window\.jQuery': 'jquery'/)
    expect(bloco).toMatch(/'_': 'lodash'/)
  })
})

describe('bundles pedidos pelos templates', () => {
  const conhecidos = ['app', ...Object.keys(entradasDeclaradas())]
  const pedidos = bundlesPedidos()

  it('V2018-EST-025: cada entrada é pedida por ao menos um template', () => {
    // `loa` chega por variável (`view.crud.frontend`), não por nome literal.
    const semUso = conhecidos.filter(nome => nome !== 'loa' && !pedidos[nome])
    expect(semUso).toEqual([])
  })

  it('V2018-EST-029: todo bundle pedido por nome literal é uma entrada', () => {
    // Um nome aqui é template pedindo bundle que o build não gera: a página termina em erro.
    const desconhecidos = Object.keys(pedidos).filter(nome => !conhecidos.includes(nome)).sort()
    expect(desconhecidos).toEqual([])
  })
})
