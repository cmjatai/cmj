import { describe, expect, it, vi } from 'vitest'

vi.mock('axios', async () => (await import('../apoio')).axiosFalso())

describe('entradas libsuserauth e construct', () => {
  it('V2018-EST-054: libsuserauth define window.tinymce e window.initTextRichEditor', async () => {
    await import('@/__apps/libsuserauth/main')

    expect(window.tinymce).toBeTypeOf('object')
    expect(window.initTextRichEditor).toBeTypeOf('function')
    expect(window.removeTinymce).toBeTypeOf('function')
  })

  it('V2018-EST-050, V2018-EST-051: depois de libsuserauth, construct monta o próprio app em #app-vue', async () => {
    document.body.innerHTML = '<div id="app-vue"><p id="marca">ok</p></div>'

    await import('@/__apps/libsuserauth/main')
    await import('@/__construct/main')

    expect(document.getElementById('marca').textContent).toBe('ok')
    expect(document.getElementById('app-vue').__vue__).toBeDefined()
  })
})
