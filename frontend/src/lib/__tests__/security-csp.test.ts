import { describe, expect, it, vi } from 'vitest'
import { NextRequest } from 'next/server'

const createServerClientMock = vi.hoisted(() => vi.fn())
vi.mock('@supabase/ssr', () => ({ createServerClient: createServerClientMock }))

describe('per-request CSP at the Proxy boundary', () => {
  it('delivers a fresh script nonce to rendering and keeps preview routes accessible', async () => {
    vi.stubEnv('NODE_ENV', 'production')
    vi.stubEnv('PRISM_PRO_PUBLIC_PREVIEW_ONLY', 'true')
    const { proxy } = await import('@/proxy')

    const first = await proxy(new NextRequest('https://www.prismpro.live/'))
    const second = await proxy(new NextRequest('https://www.prismpro.live/'))
    const policy = first.headers.get('content-security-policy') ?? ''
    const nonce = policy.match(/script-src[^;]*'nonce-([^']+)'/)?.[1]

    expect(first.status).toBe(200)
    expect(nonce).toBeTruthy()
    expect(policy).not.toMatch(/script-src[^;]*'unsafe-inline'/)
    expect(policy).toContain("frame-ancestors 'none'")
    expect(policy).toContain("object-src 'none'")
    expect(second.headers.get('content-security-policy')).not.toBe(policy)
    expect(first.headers.get('x-middleware-request-x-nonce')).toBe(nonce)
    expect(first.headers.get('x-middleware-request-content-security-policy')).toBe(policy)
  })

  it('preserves the CSP on public-preview auth redirects', async () => {
    vi.stubEnv('NODE_ENV', 'production')
    vi.stubEnv('PRISM_PRO_PUBLIC_PREVIEW_ONLY', 'true')
    const { proxy } = await import('@/proxy')

    const response = await proxy(new NextRequest('https://www.prismpro.live/login'))

    expect(response.status).toBe(307)
    expect(response.headers.get('location')).toBe('https://www.prismpro.live/')
    expect(response.headers.get('cache-control')).toContain('no-store')
    expect(response.headers.get('content-security-policy')).toMatch(/'nonce-[^']+'/)
  })

  it('keeps nonce propagation and refreshed cookies through Supabase session handling', async () => {
    vi.stubEnv('NODE_ENV', 'production')
    vi.stubEnv('PRISM_PRO_PUBLIC_PREVIEW_ONLY', 'false')
    vi.stubEnv('NEXT_PUBLIC_SUPABASE_URL', 'https://project.supabase.co')
    vi.stubEnv('NEXT_PUBLIC_SUPABASE_ANON_KEY', 'publishable-key')
    createServerClientMock.mockImplementation((_url, _key, options) => ({
      auth: {
        getClaims: async () => {
          options.cookies.setAll(
            [{ name: 'sb-session', value: 'refreshed', options: { path: '/' } }],
            { 'Cache-Control': 'private, no-store' },
          )
          return { data: { claims: { sub: 'user-123' } }, error: null }
        },
      },
    }))
    const { proxy } = await import('@/proxy')

    const response = await proxy(new NextRequest('https://www.prismpro.live/dashboard'))
    const policy = response.headers.get('content-security-policy') ?? ''
    const nonce = policy.match(/script-src[^;]*'nonce-([^']+)'/)?.[1]

    expect(response.status).toBe(200)
    expect(response.cookies.get('sb-session')?.value).toBe('refreshed')
    expect(response.headers.get('cache-control')).toContain('no-store')
    expect(response.headers.get('x-middleware-request-x-nonce')).toBe(nonce)
    expect(response.headers.get('x-middleware-request-content-security-policy')).toBe(policy)
  })
})
