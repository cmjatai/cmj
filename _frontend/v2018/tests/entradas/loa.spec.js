import { describe, expect, it, vi } from 'vitest'

vi.mock('axios', async () => (await import('../apoio')).axiosFalso())

describe('entrada loa', () => {
  it('V2018-EST-052: expõe o singleton em window.AppLOA e só o executa onde há .container-loa', async () => {
    const AppLOA = (await import('@/__apps/loa/AppLOA')).default
    const run = vi.spyOn(AppLOA, 'run').mockImplementation(() => {})

    await import('@/__apps/loa/main')
    await new Promise(resolve => window.$(resolve))

    expect(window.AppLOA).toBe(AppLOA)
    expect(run).not.toHaveBeenCalled()
  })
})
