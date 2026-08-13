import { beforeEach, describe, expect, it, vi } from 'vitest'
import { NextRequest } from 'next/server'

const createServerClientMock = vi.hoisted(() => vi.fn())

vi.mock('@supabase/ssr', () => ({
  createServerClient: createServerClientMock,
}))

describe('Supabase session Proxy', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.stubEnv('NODE_ENV', 'production')
    vi.stubEnv('NEXT_PUBLIC_SUPABASE_URL', 'https://project.supabase.co')
    vi.stubEnv('NEXT_PUBLIC_SUPABASE_ANON_KEY', 'publishable-key')
  })

  it('preserves refreshed cookies and anti-cache headers on auth redirects', async () => {
    createServerClientMock.mockImplementation((_url, _key, options) => ({
      auth: {
        getClaims: async () => {
          options.cookies.setAll(
            [{ name: 'sb-session', value: 'refreshed', options: { path: '/' } }],
            {
              'Cache-Control': 'private, no-store',
              Expires: '0',
              Pragma: 'no-cache',
            },
          )
          return { data: { claims: null }, error: null }
        },
      },
    }))
    const { updateSession } = await import('@/lib/supabase-proxy')

    const response = await updateSession(
      new NextRequest('https://www.prismpro.live/dashboard/resume'),
    )

    expect(response.status).toBe(307)
    expect(response.headers.get('location')).toBe('https://www.prismpro.live/')
    expect(response.cookies.get('sb-session')?.value).toBe('refreshed')
    expect(response.headers.get('cache-control')).toContain('private')
    expect(response.headers.get('cache-control')).toContain('no-store')
  })

  it('uses verified claims for authenticated onboarding routing', async () => {
    createServerClientMock.mockReturnValue({
      auth: {
        getClaims: async () => ({
          data: {
            claims: {
              sub: 'user-123',
              user_metadata: {
                onboarding_completed: true,
                oauth_provider: 'google',
              },
            },
          },
          error: null,
        }),
      },
    })
    const { updateSession } = await import('@/lib/supabase-proxy')

    const response = await updateSession(
      new NextRequest('https://www.prismpro.live/onboarding'),
    )

    expect(response.status).toBe(307)
    expect(response.headers.get('location')).toBe(
      'https://www.prismpro.live/dashboard',
    )
    expect(response.headers.get('cache-control')).toContain('no-store')
  })

  it('fails closed when claim verification is unavailable', async () => {
    createServerClientMock.mockReturnValue({
      auth: {
        getClaims: async () => {
          throw new Error('JWKS unavailable')
        },
      },
    })
    const { updateSession } = await import('@/lib/supabase-proxy')

    const response = await updateSession(
      new NextRequest('https://www.prismpro.live/dashboard'),
    )

    expect(response.status).toBe(307)
    expect(response.headers.get('location')).toBe('https://www.prismpro.live/')
  })
})
