// Arquivo separado de construct.spec.js: a falha de carregamento fica guardada no cache de módulos.
import { describe, expect, it } from 'vitest'

describe('entrada construct sem libsuserauth', () => {
  it('V2018-EST-051: o editor de texto de construct não carrega sem o tinymce global', async () => {
    expect(window.tinymce).toBeUndefined()
    await expect(import('@/__construct/apps/sigad/components/TpdTexto')).rejects.toThrow(/tinymce/)
  })
})
