import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'

import { afterEach, describe, expect, it } from 'vitest'

import { atualizar, mesAtual, proximaVersao } from '../../../versao.mjs'

// Versionamento de produção dos frontends (docs/specs/infra/versionamento.md).
// O script de versão é um só para os três frontends; os service workers são lidos como texto.

const FRONTEND = path.resolve(__dirname, '../../..')
const NOV = new Date('2026-11-15T12:00:00-03:00')

describe('versão de build dos frontends', () => {
  let pasta

  afterEach(() => {
    if (pasta) fs.rmSync(pasta, { recursive: true, force: true })
    pasta = undefined
  })

  it('INFRA-VER-007: soma 1 no mesmo mês e frontend, e volta a 1 nos outros casos', () => {
    expect(proximaVersao('v6.2026.11.3', 'v6', NOV)).toBe('v6.2026.11.4')
    expect(proximaVersao('v6.2026.10.9', 'v6', NOV)).toBe('v6.2026.11.1')
    expect(proximaVersao('v8.2026.11.3', 'v6', NOV)).toBe('v6.2026.11.1')
    expect(proximaVersao('v6.26.05.24.1', 'v6', NOV)).toBe('v6.2026.11.1')
    expect(proximaVersao(undefined, 'v2018', NOV)).toBe('v2018.2026.11.1')
    expect(() => proximaVersao('v6.2026.11.1', 'v9', NOV)).toThrow('frontend desconhecido')
  })

  it('INFRA-VER-007: o mês é o de São Paulo', () => {
    // 01/12 às 01h em UTC ainda é 30/11 em São Paulo.
    expect(mesAtual(new Date('2026-12-01T01:00:00Z'))).toBe('2026.11')
    expect(mesAtual(new Date('2026-12-01T03:00:00Z'))).toBe('2026.12')
  })

  it('INFRA-VER-007: grava no package.json e no package-lock.json, sem mexer no resto', () => {
    pasta = fs.mkdtempSync(path.join(os.tmpdir(), 'versao-'))
    const pkg = '{\n  "name": "x",\n  "version": "v6.2026.11.1",\n  "files": ["a", "b"]\n}\n'
    const lock = {
      name: 'x',
      version: 'v6.2026.11.1',
      lockfileVersion: 3,
      packages: { '': { name: 'x', version: 'v6.2026.11.1' }, 'node_modules/y': { version: '1.0.0' } }
    }
    fs.writeFileSync(path.join(pasta, 'package.json'), pkg)
    fs.writeFileSync(path.join(pasta, 'package-lock.json'), JSON.stringify(lock, null, 2) + '\n')

    expect(atualizar(pasta, 'v6', NOV)).toEqual({ anterior: 'v6.2026.11.1', versao: 'v6.2026.11.2' })

    expect(fs.readFileSync(path.join(pasta, 'package.json'), 'utf8'))
      .toBe(pkg.replace('v6.2026.11.1', 'v6.2026.11.2'))
    const novo = JSON.parse(fs.readFileSync(path.join(pasta, 'package-lock.json'), 'utf8'))
    expect(novo.version).toBe('v6.2026.11.2')
    expect(novo.packages[''].version).toBe('v6.2026.11.2')
    expect(novo.packages['node_modules/y'].version).toBe('1.0.0')
  })

  it('INFRA-VER-007: o prebuild de cada frontend chama o script com o nome dele', () => {
    for (const fe of ['v2018', 'v6', 'v8']) {
      const scripts = JSON.parse(fs.readFileSync(path.join(FRONTEND, fe, 'package.json'), 'utf8')).scripts
      expect(scripts.prebuild).toBe(`node ../versao.mjs ${fe}`)
    }
  })
})

describe('service workers', () => {
  const ler = rel => fs.readFileSync(path.join(FRONTEND, rel), 'utf8')

  it('INFRA-VER-008: o SW de cada frontend recebe a versão do package.json no build', () => {
    for (const fe of ['v2018', 'v6', 'v8']) {
      expect(ler(`${fe}/src/service-worker.js`)).toMatch(/^self\.PORTALCMJ_VERSAO = __PORTALCMJ_VERSAO__$/m)
    }
    for (const fe of ['v6', 'v8']) {
      const config = ler(`${fe}/vite.config.js`)
      expect(config).toContain('readFileSync(new URL(\'./package.json\', import.meta.url))')
      expect(config).toContain('__PORTALCMJ_VERSAO__: JSON.stringify(VERSAO)')
    }
    expect(ler('v2018/vue.config.js'))
      .toContain('__PORTALCMJ_VERSAO__: JSON.stringify(require(\'./package.json\').version)')
  })

  it('INFRA-VER-009: o SW do v2018 ativa ao instalar e assume as páginas abertas', () => {
    const sw = ler('v2018/src/service-worker.js')
    expect(sw).toMatch(/addEventListener\('install',[^]*?self\.skipWaiting\(\)/)
    expect(sw).toMatch(/addEventListener\('activate',[^]*?self\.clients\.claim\(\)/)
  })
})
