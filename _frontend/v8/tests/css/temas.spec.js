// Regras do CSS dos temas, conferidas lendo os arquivos (docs/specs/v8/temas.md).
import fs from 'fs'
import path from 'path'
import { describe, expect, it } from 'vitest'
import {
  PASTA_CSS,
  PASTA_TEMAS,
  RAIZ,
  arquivosDoTema,
  blocos,
  blocosDeCor,
  cores,
  ler,
  pastasDeTema,
  semComentarios
} from './apoio'

const OFICIAL = path.join(PASTA_TEMAS, 'oficial')
const tokensOficial = () => ler(path.join(OFICIAL, 'tokens.css'))

// Todo CSS e todo .vue de src/, menos os assets.
function fontes(pasta = path.join(RAIZ, 'src')) {
  return fs.readdirSync(pasta, { withFileTypes: true }).flatMap(item => {
    const caminho = path.join(pasta, item.name)
    if (item.isDirectory()) {
      return item.name === 'assets' ? [] : fontes(caminho)
    }
    return /\.(css|vue)$/.test(item.name) ? [caminho] : []
  })
}

const ehTokens = caminho => /[\\/]css[\\/]temas[\\/][a-z][a-z0-9-]*[\\/]tokens\.css$/.test(caminho)

describe('CSS dos temas', () => {
  it('V8-TEMA-010: o oficial reúne o CSS padrão e é o único com @theme', () => {
    const indice = semComentarios(ler(path.join(OFICIAL, 'index.css')))
    const importados = [...indice.matchAll(/@import\s+"\.\/([a-z-]+\.css)"/g)].map(m => m[1])
    expect(importados[0]).toBe('tokens.css')
    ;['shell.css', 'componentes.css', 'overlays.css'].forEach(arquivo => {
      expect(importados).toContain(arquivo)
    })
    importados.forEach(arquivo => expect(fs.existsSync(path.join(OFICIAL, arquivo)), arquivo).toBe(true))
    expect(arquivosDoTema('oficial').map(f => path.basename(f)).sort()).toEqual(
      ['index.css', ...importados].sort()
    )

    const comTheme = fontes().filter(f => /@theme\b/.test(semComentarios(ler(f))))
    expect(comTheme.map(f => path.relative(PASTA_CSS, f))).toEqual(['temas/oficial/tokens.css'])
  })

  it('V8-TEMA-011: camadas e movimento só têm valor no oficial', () => {
    const fora = pastasDeTema()
      .filter(nome => nome !== 'oficial')
      .flatMap(nome => arquivosDoTema(nome))
      .filter(f => /^\s*--(?:z-[a-z]+|duracao|curva)\s*:/m.test(ler(f)))
    expect(fora).toEqual([])
    expect(tokensOficial()).toMatch(/--z-popover:\s*\d+/)
    expect(tokensOficial()).toMatch(/--duracao:\s*\d+ms/)
  })

  it('V8-TEMA-013: no oficial, toda cor tem valor no claro, no escuro e sem modo escolhido', () => {
    const { claro, escuro, sistema } = blocosDeCor(tokensOficial(), ':root')
    expect(cores(claro.corpo).length).toBeGreaterThan(15)
    expect(cores(escuro.corpo)).toEqual(cores(claro.corpo))
    expect(cores(sistema.corpo)).toEqual(cores(claro.corpo))
    expect(claro.corpo).toMatch(/color-scheme:\s*light/)
    expect(escuro.corpo).toMatch(/color-scheme:\s*dark/)
    expect(sistema.corpo).toMatch(/color-scheme:\s*dark/)
  })

  it('V8-TEMA-016: o @theme do oficial expõe cores, fontes e raios por var() e tira a paleta', () => {
    const tema = blocos(tokensOficial()).find(b => b.seletor === '@theme inline')
    expect(tema).toBeDefined()
    const corpo = tema.corpo
    expect(corpo).toMatch(/--color-\*:\s*initial/)
    expect(corpo).toMatch(/--radius-\*:\s*initial/)
    const valores = [...corpo.matchAll(/(--[a-z-]+)(?<!\*)\s*:\s*([^;]+);/g)]
      .filter(m => !m[2].trim().startsWith('initial'))
    expect(valores.length).toBeGreaterThan(15)
    valores.forEach(([, nome, valor]) => expect(valor.trim(), nome).toMatch(/^var\(--(cor|fonte|raio)/))
    ;['--color-primaria', '--font-sans', '--font-mono', '--radius-md'].forEach(nome => {
      expect(valores.map(m => m[1])).toContain(nome)
    })
  })

  it('V8-TEMA-017: fonte, sombra e raio vêm de token', () => {
    const regras = {
      'font-family': /^(var\(--fonte-[a-z-]+\)|inherit)$/,
      'box-shadow': /^(var\(--sombra-[a-z0-9-]+\)|none)$/,
      'border-radius': /^(var\(--raio(-[a-z]+)?\)|0|50%|inherit)$/
    }
    const achadas = []
    fontes()
      .filter(f => !ehTokens(f))
      .forEach(caminho => {
        semComentarios(ler(caminho))
          .split('\n')
          .forEach((linha, i) => {
            const m = /^\s*(font-family|box-shadow|border-radius)\s*:\s*([^;]+);/.exec(linha)
            if (m && !regras[m[1]].test(m[2].trim())) {
              achadas.push(`${path.relative(RAIZ, caminho)}:${i + 1}: ${linha.trim()}`)
            }
          })
      })
    expect(achadas).toEqual([])
    ;['--fonte-base', '--fonte-mono', '--raio-sm', '--raio-lg', '--sombra-1', '--sombra-3'].forEach(nome => {
      expect(tokensOficial()).toMatch(new RegExp(`${nome}:`))
    })
  })
})
