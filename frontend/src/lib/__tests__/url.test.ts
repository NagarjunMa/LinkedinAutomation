import { afterEach, describe, expect, it, vi } from 'vitest'

describe('url helpers', () => {
  const originalEnv = { ...process.env }

  afterEach(() => {
    vi.resetModules()
    process.env = { ...originalEnv }
  })

  it('normalizes a bare production domain into an absolute HTTPS origin', async () => {
    const { normalizeAppOrigin } = await import('../url')

    expect(normalizeAppOrigin('app.example.com')).toBe('https://app.example.com')
    expect(normalizeAppOrigin('https://app.example.com/')).toBe('https://app.example.com')
  })

  it('prefers NEXT_PUBLIC_FRONTEND_URL and normalizes missing protocol', async () => {
    process.env.NEXT_PUBLIC_FRONTEND_URL = 'app.example.com'
    process.env.NEXT_PUBLIC_SITE_URL = 'https://example.com'

    const { getConfiguredAppOrigin } = await import('../url')

    expect(getConfiguredAppOrigin()).toBe('https://app.example.com')
  })

  it('falls back to the request origin when configured URLs are empty', async () => {
    delete process.env.NEXT_PUBLIC_FRONTEND_URL
    delete process.env.NEXT_PUBLIC_SITE_URL

    const { getConfiguredAppOrigin } = await import('../url')

    expect(getConfiguredAppOrigin('https://preview.example.com')).toBe(
      'https://preview.example.com'
    )
  })
})
