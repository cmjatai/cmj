// Versão de build dos frontends: <frontend>.AAAA.MM.N (docs/specs/infra/versionamento.md).
// Chamado pelo "prebuild" de cada frontend, na pasta dele: node ../versao.mjs <v2018|v6|v8>
// N soma 1 quando a versão anterior é do mesmo frontend e do mês atual em São Paulo; senão volta a 1.

import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

export const FRONTENDS = ['v2018', 'v6', 'v8']

export function mesAtual (agora = new Date()) {
  const partes = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'America/Sao_Paulo', year: 'numeric', month: '2-digit'
  }).formatToParts(agora)
  const valor = tipo => partes.find(p => p.type === tipo).value
  return `${valor('year')}.${valor('month')}`
}

export function proximaVersao (anterior, frontend, agora = new Date()) {
  if (!FRONTENDS.includes(frontend)) {
    throw new Error(`frontend desconhecido: ${frontend}`)
  }
  const prefixo = `${frontend}.${mesAtual(agora)}.`
  const n = typeof anterior === 'string' && anterior.startsWith(prefixo)
    ? Number(anterior.slice(prefixo.length))
    : NaN
  return prefixo + (Number.isInteger(n) && n > 0 ? n + 1 : 1)
}

// Grava a versão nova no package.json (só a linha do "version", sem reformatar o arquivo) e no
// package-lock.json (raiz e packages[""], no formato que o próprio npm grava).
export function atualizar (pasta, frontend, agora = new Date()) {
  const arqPkg = path.join(pasta, 'package.json')
  const textoPkg = fs.readFileSync(arqPkg, 'utf8')
  const anterior = JSON.parse(textoPkg).version
  const versao = proximaVersao(anterior, frontend, agora)

  const RE_VERSAO = /^(\s*"version"\s*:\s*)"[^"]*"/m
  if (!RE_VERSAO.test(textoPkg)) {
    throw new Error(`${arqPkg} sem o campo "version"`)
  }
  fs.writeFileSync(arqPkg, textoPkg.replace(RE_VERSAO, `$1${JSON.stringify(versao)}`))

  const arqLock = path.join(pasta, 'package-lock.json')
  if (fs.existsSync(arqLock)) {
    const lock = JSON.parse(fs.readFileSync(arqLock, 'utf8'))
    lock.version = versao
    if (lock.packages && lock.packages['']) {
      lock.packages[''].version = versao
    }
    fs.writeFileSync(arqLock, JSON.stringify(lock, null, 2) + '\n')
  }
  return { anterior, versao }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const frontend = process.argv[2]
  try {
    const { anterior, versao } = atualizar(process.cwd(), frontend)
    console.log(`versão ${frontend}: ${anterior} -> ${versao}`)
  } catch (e) {
    console.error(`erro: ${e.message}`)
    process.exit(1)
  }
}
