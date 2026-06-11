import { afterEach, describe, expect, it, vi } from 'vitest'

describe('url helpers', () => {
  const originalEnv = { ...process.env }

  afterEach(() => {
    vi.resetModules()
    process.env = { ...originalEnv }
  })

  it('normalizes a bare production domain into an absolute HTTPS origin', async () => {
    const { normalizeAppOrigin } = await import('../url')

    expect(normalizeAppOrigin('www.prismpro.live')).toBe('https://www.prismpro.live')
    expect(normalizeAppOrigin('https://www.prismpro.live/')).toBe('https://www.prismpro.live')
  })

  it('prefers NEXT_PUBLIC_FRONTEND_URL and normalizes missing protocol', async () => {
    process.env.NEXT_PUBLIC_FRONTEND_URL = 'www.prismpro.live'
    process.env.NEXT_PUBLIC_SITE_URL = 'https://prismpro.live'

    const { getConfiguredAppOrigin } = await import('../url')

    expect(getConfiguredAppOrigin()).toBe('https://www.prismpro.live')
  })

  it('falls back to the request origin when configured URLs are empty', async () => {
    delete process.env.NEXT_PUBLIC_FRONTEND_URL
    delete process.env.NEXT_PUBLIC_SITE_URL

    const { getConfiguredAppOrigin } = await import('../url')

    expect(getConfiguredAppOrigin('https://preview.prismpro.live')).toBe(
      'https://preview.prismpro.live'
    )
  })
})
