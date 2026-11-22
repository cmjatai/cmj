// Leitura do CSS dos temas para os testes: pastas, arquivos e blocos por chaves.
import fs from 'fs'
import path from 'path'

export const RAIZ = path.resolve(__dirname, '../..')
export const PASTA_CSS = path.join(RAIZ, 'src/css')
export const PASTA_TEMAS = path.join(PASTA_CSS, 'temas')

export const ler = caminho => fs.readFileSync(caminho, 'utf8')

// Nomes das pastas de tema, em ordem alfabética.
export function pastasDeTema() {
  return fs
    .readdirSync(PASTA_TEMAS, { withFileTypes: true })
    .filter(item => item.isDirectory())
    .map(item => item.name)
    .sort()
}

// Arquivos .css de um tema, com o caminho completo.
export function arquivosDoTema(nome) {
  const pasta = path.join(PASTA_TEMAS, nome)
  return fs
    .readdirSync(pasta)
    .filter(arquivo => arquivo.endsWith('.css'))
    .map(arquivo => path.join(pasta, arquivo))
}

export const semComentarios = css => css.replace(/\/\*[\s\S]*?\*\//g, '')

// Blocos do CSS, com o seletor (ou a at-rule), o corpo, a at-rule que os contém e a profundidade
// (0 no topo do arquivo). Desce nas at-rules (`@media`, `@layer`) e nas regras aninhadas.
export function blocos(css, pai = '', nivel = 0) {
  const texto = semComentarios(css)
  const achados = []
  let inicio = 0
  while (inicio < texto.length) {
    const abre = texto.indexOf('{', inicio)
    if (abre === -1) {
      break
    }
    const antes = Math.max(texto.lastIndexOf('}', abre), texto.lastIndexOf(';', abre), inicio - 1)
    const seletor = texto.slice(antes + 1, abre).trim()
    let abertas = 1
    let fim = abre + 1
    while (fim < texto.length && abertas) {
      if (texto[fim] === '{') {
        abertas++
      } else if (texto[fim] === '}') {
        abertas--
      }
      fim++
    }
    const corpo = texto.slice(abre + 1, fim - 1)
    achados.push({ seletor, corpo, pai, nivel })
    if (corpo.includes('{')) {
      achados.push(...blocos(corpo, seletor.startsWith('@') ? seletor : pai, nivel + 1))
    }
    inicio = fim
  }
  return achados
}

// Declarações do próprio bloco, sem as dos blocos aninhados.
export function declaracoes(corpo) {
  return semComentarios(corpo).replace(/\{[^{}]*\}/g, '')
}

// Nomes das variáveis `--cor-*` definidas no próprio bloco, ordenados.
export function cores(corpo) {
  return [...declaracoes(corpo).matchAll(/(--cor-[a-z0-9-]+)\s*:/g)].map(m => m[1]).sort()
}

// Nomes de todas as variáveis definidas no próprio bloco, ordenados.
export function variaveis(corpo) {
  return [...declaracoes(corpo).matchAll(/(--[a-z][a-z0-9-]*)\s*:/g)].map(m => m[1]).sort()
}

// Os três blocos de cor de um tema: claro, escuro e o que vale sem modo escolhido.
export function blocosDeCor(css, seletorRaiz) {
  const todos = blocos(css)
  const escuroDoSistema = pai => /prefers-color-scheme:\s*dark/.test(pai)
  const achar = (seletor, condicao = pai => pai === '') =>
    todos.find(bloco => bloco.seletor === seletor && condicao(bloco.pai))
  return {
    claro: achar(seletorRaiz),
    escuro: achar(`${seletorRaiz}[data-modo="escuro"]`),
    sistema: achar(`${seletorRaiz}:not([data-modo])`, escuroDoSistema)
  }
}

// Partes de uma lista de seletores, separadas pelas vírgulas que não estão entre parênteses.
export function partesDoSeletor(seletor) {
  const partes = []
  let nivel = 0
  let atual = ''
  for (const caractere of seletor) {
    if (caractere === '(') {
      nivel++
    } else if (caractere === ')') {
      nivel--
    }
    if (caractere === ',' && nivel === 0) {
      partes.push(atual.trim())
      atual = ''
    } else {
      atual += caractere
    }
  }
  partes.push(atual.trim())
  return partes.filter(Boolean)
}
