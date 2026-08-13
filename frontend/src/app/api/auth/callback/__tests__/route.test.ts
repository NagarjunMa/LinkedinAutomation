import { beforeEach, describe, expect, it, vi } from 'vitest'
import { NextRequest } from 'next/server'

const createServerClientMock = vi.hoisted(() => vi.fn())
const exchangeCodeMock = vi.hoisted(() => vi.fn())

vi.mock('@/lib/supabase-server', () => ({
  createServerSupabaseClientWithResponse: createServerClientMock,
}))

describe('OAuth callback', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.stubEnv('NEXT_PUBLIC_FRONTEND_URL', 'https://www.prismpro.live')
    createServerClientMock.mockImplementation(async (response) => {
      response.cookies.set('sb-session', 'fresh-session', { path: '/' })
      response.headers.set('Cache-Control', 'private, no-store')
      return { auth: { exchangeCodeForSession: exchangeCodeMock } }
    })
  })

  it('exchanges the code, preserves auth cookies, and rejects an external next URL', async () => {
    exchangeCodeMock.mockResolvedValue({
      data: { session: { access_token: 'not-logged' } },
      error: null,
    })
    const { GET } = await import('@/app/api/auth/callback/route')

    const response = await GET(
      new NextRequest(
        'https://www.prismpro.live/api/auth/callback?code=oauth-code&next=//attacker.example',
      ),
    )

    expect(exchangeCodeMock).toHaveBeenCalledWith('oauth-code')
    expect(response.headers.get('location')).toBe(
      'https://www.prismpro.live/dashboard',
    )
    expect(response.cookies.get('sb-session')?.value).toBe('fresh-session')
    expect(response.headers.get('cache-control')).toContain('no-store')
  })

  it('returns a stable error without exposing provider details', async () => {
    exchangeCodeMock.mockResolvedValue({
      data: { session: null },
      error: { message: 'PKCE verifier internals' },
    })
    const { GET } = await import('@/app/api/auth/callback/route')

    const response = await GET(
      new NextRequest(
        'https://www.prismpro.live/api/auth/callback?code=invalid-code',
      ),
    )

    expect(response.headers.get('location')).toBe(
      'https://www.prismpro.live/login?error=session_failed',
    )
    expect(response.headers.get('location')).not.toContain('PKCE')
    expect(response.headers.get('cache-control')).toContain('no-store')
  })
})
