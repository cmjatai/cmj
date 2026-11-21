// Regra conferida lendo os arquivos: configuração do npm nos três frontends.
import fs from 'fs'
import path from 'path'
import { describe, expect, it } from 'vitest'

const FRONTENDS = path.resolve(__dirname, '../../..')

describe('instalação de dependências', () => {
  it.each(['v2018', 'v6', 'v8'])('V2018-EST-016: %s só instala versões publicadas há mais de 7 dias', frontend => {
    const npmrc = fs.readFileSync(path.join(FRONTENDS, frontend, '.npmrc'), 'utf8')
    expect(npmrc).toMatch(/^min-release-age=7$/m)
  })
})
