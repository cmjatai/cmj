// Regras conferidas lendo os arquivos do v8: camadas, cores e restos do v6.
import fs from 'fs'
import path from 'path'
import { describe, expect, it } from 'vitest'

const RAIZ = path.resolve(__dirname, '../..')
const TEMPLATES = path.resolve(RAIZ, '../../_templates/v8')

function arquivos(pasta, extensoes) {
  const achados = []
  if (!fs.existsSync(pasta)) {
    return achados
  }
  fs.readdirSync(pasta, { withFileTypes: true }).forEach(item => {
    const caminho = path.join(pasta, item.name)
    if (item.isDirectory()) {
      if (item.name !== 'assets') {
        achados.push(...arquivos(caminho, extensoes))
      }
    } else if (extensoes.includes(path.extname(item.name))) {
      achados.push(caminho)
    }
  })
  return achados
}

const fontes = [
  ...arquivos(path.join(RAIZ, 'src'), ['.js', '.vue', '.css']),
  ...arquivos(TEMPLATES, ['.html'])
]
const relativo = caminho => path.relative(path.resolve(RAIZ, '../..'), caminho)
const ler = caminho => fs.readFileSync(caminho, 'utf8')
const ehTokens = caminho => caminho.endsWith(path.join('css', 'tokens.css'))

function ocorrencias(expressao, filtro = () => true) {
  const achadas = []
  fontes.filter(filtro).forEach(caminho => {
    ler(caminho).split('\n').forEach((linha, i) => {
      if (expressao.test(linha)) {
        achadas.push(`${relativo(caminho)}:${i + 1}: ${linha.trim()}`)
      }
    })
  })
  return achadas
}

describe('fontes do v8', () => {
  it('há fontes para conferir', () => {
    expect(fontes.length).toBeGreaterThan(20)
    expect(fontes.some(f => f.endsWith('.html'))).toBe(true)
  })

  it('V8-OVL-001: os tokens de camada existem e estão em ordem crescente', () => {
    const tokens = ler(path.join(RAIZ, 'src/css/tokens.css'))
    const valor = nome => Number(new RegExp(`--z-${nome}:\\s*(\\d+)`).exec(tokens)[1])
    const ordem = ['base', 'sticky', 'drawer', 'modal', 'toast', 'popover'].map(valor)
    expect(ordem).toEqual([...ordem].sort((a, b) => a - b))
    expect(new Set(ordem).size).toBe(6)
  })

  it('V8-OVL-002: nenhum z-index tem valor literal', () => {
    // Em CSS: z-index sem var(--z-...). Em classes: z-10, z-[10]. Em estilo JS: zIndex.
    const semToken = ocorrencias(/z-index\s*:(?!\s*(?:var\(--z-|calc\(var\(--z-))/)
    const classes = ocorrencias(/(?:^|[\s"'`:])-?z-(?:\d+|\[)/, f => !f.endsWith('.css'))
    const emJs = ocorrencias(/zIndex/)
    expect([...semToken, ...classes, ...emJs]).toEqual([])
  })

  it('V8-SHELL-042: não há cor literal fora de tokens.css', () => {
    const hex = /#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b/
    const funcoes = /\b(?:rgba?|hsla?|oklch|oklab)\(/
    const achadas = [
      ...ocorrencias(hex, f => !ehTokens(f)),
      ...ocorrencias(funcoes, f => !ehTokens(f))
    ]
      // A cor da barra do navegador precisa estar no HTML, antes do CSS.
      .filter(linha => !/<meta name="theme-color"/.test(linha))
      // Entidades numéricas e âncoras não são cores.
      .filter(linha => !/&#\d+;/.test(linha))
    expect(achadas).toEqual([])
  })

  it('V8-SHELL-042: os dois temas definem as mesmas cores', () => {
    const tokens = ler(path.join(RAIZ, 'src/css/tokens.css'))
    const cores = bloco => [...bloco.matchAll(/(--cor-[a-z0-9-]+)\s*:/g)].map(m => m[1]).sort()
    const claro = /:root\s*\{([\s\S]*?)\n\}/.exec(tokens)[1]
    const escuro = /:root\[data-theme="escuro"\]\s*\{([\s\S]*?)\n\}/.exec(tokens)[1]
    const sistema = /:root:not\(\[data-theme\]\)\s*\{([\s\S]*?)\n {2}\}/.exec(tokens)[1]
    expect(cores(claro).length).toBeGreaterThan(10)
    expect(cores(escuro)).toEqual(cores(claro))
    expect(cores(sistema)).toEqual(cores(claro))
  })

  it('V8-OVL-026: a duração das animações é um token, zerado com prefers-reduced-motion', () => {
    const tokens = ler(path.join(RAIZ, 'src/css/tokens.css'))
    expect(/prefers-reduced-motion:\s*reduce\)\s*\{\s*:root\s*\{\s*--duracao:\s*0ms/.test(tokens)).toBe(true)
    const literais = ocorrencias(/(?:transition|animation)[a-z-]*\s*:[^;]*\b\d+(?:\.\d+)?m?s\b/, f => f.endsWith('.css') && !ehTokens(f))
    expect(literais).toEqual([])
  })

  it('V8-ARQ-031: o build não usa o compilador de templates nem delimitadores no HTML', () => {
    const config = ler(path.join(RAIZ, 'vite.config.js'))
    expect(config).not.toMatch(/esm-bundler/)
    expect(ocorrencias(/delimiters|<cmj-app|\[\[\s*[a-zA-Z_$]/)).toEqual([])
    expect(ocorrencias(/\bv-html\b/)).toEqual([])
  })

  it('V8-ARQ-050: o Tailwind lê as classes de src e dos templates do v8', () => {
    const config = ler(path.join(RAIZ, 'vite.config.js'))
    const css = ler(path.join(RAIZ, 'src/css/app.css'))
    expect(config).toMatch(/@tailwindcss\/vite/)
    const origem = /@source\s+"([^"]+)"/.exec(css)[1]
    expect(path.resolve(RAIZ, 'src/css', origem)).toBe(TEMPLATES)
  })

  it('V8-ARQ-051: os tokens ficam em um único arquivo', () => {
    const definicoes = ocorrencias(/^\s*--(?:cor|z|duracao|curva|largura|altura|raio|deslocamento)-?[a-z0-9-]*\s*:/, f => f.endsWith('.css') && !ehTokens(f))
    expect(definicoes).toEqual([])
  })

  it('V8-ARQ-052: os primitivos de overlay vêm do Reka UI', () => {
    const moldura = ler(path.join(RAIZ, 'src/overlays/OverlayFrame.vue'))
    expect(moldura).toMatch(/from 'reka-ui'/)
    expect(moldura).toMatch(/DialogContent/)
  })

  it('V8-ARQ-055: os restos do v6 saíram', () => {
    const src = caminho => path.join(RAIZ, 'src', caminho)
    ;['sw.js', 'registerComponents.js', 'routers', 'scss'].forEach(nome => {
      expect(fs.existsSync(src(nome)), nome).toBe(false)
    })
    expect(ocorrencias(/bootstrap|data-bs-|fortawesome|jQuery|\$\(/)).toEqual([])
    const eslint = ler(path.join(RAIZ, 'eslint.config.js'))
    expect(eslint).not.toMatch(/bootstrap|EventBus/)
    expect(ler(path.join(RAIZ, 'vite.config.js'))).not.toMatch(/fortawesome/)
    expect(JSON.parse(ler(path.join(RAIZ, 'package.json'))).dependencies.axios).toBeUndefined()
  })

  it('V8-ARQ-040: rotas, ilhas, painéis e modals são importados sob demanda', () => {
    ;['ilhas.js', 'zonas.js', 'paineis.js', 'modais.js'].forEach(nome => {
      const fonte = ler(path.join(RAIZ, 'src/core', nome))
      expect(fonte, nome).toMatch(/\(\) => import\(/)
      expect(fonte, nome).not.toMatch(/^import .*modules\//m)
    })
  })

  it('V8-ARQ-005: fora de /v8/, o frontend só chama /api e /ws/sync/', () => {
    // Literais que começam um caminho. Pedaço concatenado depois de `+` ou de `}` não conta.
    const literais = ocorrencias(/(?<![+}]\s?)['"`]\/(?!v8\/|api\b|api\/|ws\/sync\/|login\/|logout\/|static\/)[a-z][a-z0-9_-]*\/[^'"`]*['"`]/, f => /\.(js|vue)$/.test(f))
      .filter(linha => !/^\S+:\d+:\s*(\/\/|\*|<!--)/.test(linha))
    expect(literais).toEqual([])
  })
})
