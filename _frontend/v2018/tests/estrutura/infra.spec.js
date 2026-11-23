// Regras da infraestrutura de testes conferidas lendo os arquivos do projeto.
import fs from 'fs'
import path from 'path'
import { describe, expect, it } from 'vitest'

const RAIZ = path.resolve(__dirname, '../..')
const REPO = path.resolve(RAIZ, '../..')
const ler = (...partes) => fs.readFileSync(path.join(...partes), 'utf8')

function arquivos (pasta, extensoes) {
  return fs.readdirSync(pasta, { withFileTypes: true }).flatMap(item => {
    const caminho = path.join(pasta, item.name)
    if (item.isDirectory()) {
      return arquivos(caminho, extensoes)
    }
    return extensoes.some(extensao => item.name.endsWith(extensao)) ? [caminho] : []
  })
}

const pacote = JSON.parse(ler(RAIZ, 'package.json'))
const BIBLIOTECAS_DE_TESTE = ['vitest', 'vite', '@vitejs/plugin-vue2', '@vue/test-utils', 'jsdom', '@rollup/plugin-inject']

// Trecho do ci.yml que define o job do v2018, até o próximo job ou o fim do arquivo.
function jobDoCi () {
  const ci = ler(REPO, '.github/workflows/ci.yml')
  const inicio = ci.indexOf('\n  frontend-v2018:')
  expect(inicio).toBeGreaterThan(-1)
  const proximo = ci.slice(inicio + 1).search(/\n {2}[\w-]+:\n/)
  return proximo === -1 ? ci.slice(inicio) : ci.slice(inicio, inicio + 1 + proximo)
}

describe('infraestrutura de testes', () => {
  it('V2018-TST-001: npm test roda o Vitest uma vez', () => {
    expect(pacote.scripts.test).toBe('vitest run')
  })

  it('V2018-TST-003, V2018-TST-021: nem a configuração nem os testes executam o vue.config.js ou leem o .env', () => {
    const fontes = [path.join(RAIZ, 'vitest.config.mjs'), ...arquivos(path.join(RAIZ, 'tests'), ['.js'])]
      .filter(caminho => caminho !== __filename)
    const suspeitos = fontes.filter(caminho => {
      const texto = fs.readFileSync(caminho, 'utf8')
      return /(require|import)\s*\(?[^\n]*vue\.config/.test(texto) || /dotenv/.test(texto) || /['"`][^'"`\n]*\.env['"`]/.test(texto)
    })
    expect(suspeitos.map(caminho => path.relative(RAIZ, caminho))).toEqual([])
  })

  it('V2018-TST-005: os testes ficam em tests/ e nenhum em src/', () => {
    expect(arquivos(path.join(RAIZ, 'src'), ['.spec.js', '.test.js'])).toEqual([])
    const pastas = fs.readdirSync(path.join(RAIZ, 'tests'), { withFileTypes: true })
      .filter(item => item.isDirectory()).map(item => item.name).sort()
    expect(pastas).toEqual(['app', 'apps', 'entradas', 'estrutura'])
    expect(ler(RAIZ, 'vitest.config.mjs')).toContain("include: ['tests/**/*.spec.js']")
  })

  it('V2018-TST-009: o CI instala com npm ci e roda npm test, sem lint nem build', () => {
    const comandos = jobDoCi().split('\n')
      .filter(linha => linha.trim().startsWith('- run:'))
      .map(linha => linha.replace(/^\s*- run:\s*/, ''))
    expect(comandos).toEqual(['npm ci', 'npm test'])
  })

  it('V2018-TST-022: o job do CI não usa segredo nem publica artefato', () => {
    const job = jobDoCi()
    expect(job).not.toMatch(/secrets\./)
    expect(job).not.toMatch(/upload-artifact|deploy/)
  })

  it('V2018-TST-023: as bibliotecas de teste ficam em devDependencies e src/ não as importa', () => {
    BIBLIOTECAS_DE_TESTE.forEach(nome => {
      expect(pacote.devDependencies[nome], nome).toBeDefined()
      expect(pacote.dependencies[nome], nome).toBeUndefined()
    })
    const importam = arquivos(path.join(RAIZ, 'src'), ['.js', '.vue']).filter(caminho =>
      /from ['"](vitest|vite|@vue\/test-utils|jsdom)['"/]/.test(fs.readFileSync(caminho, 'utf8')))
    expect(importam).toEqual([])
  })
})
