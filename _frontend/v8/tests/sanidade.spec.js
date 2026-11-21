import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { DialogContent, DialogPortal, DialogRoot, DialogTitle } from 'reka-ui'
import { h } from 'vue'

describe('ambiente de testes', () => {
  it('monta um dialog do Reka UI no jsdom', async () => {
    const w = mount({
      render: () => h(DialogRoot, { open: true }, () => h(DialogPortal, null, () =>
        h(DialogContent, { 'aria-describedby': undefined }, () => h(DialogTitle, null, () => 'Título'))))
    }, { attachTo: document.body })
    await new Promise(r => setTimeout(r, 20))
    const d = document.querySelector('[role="dialog"]')
    expect(d).not.toBeNull()
    expect(d.getAttribute('aria-labelledby')).toBeTruthy()
    w.unmount()
  })
})
