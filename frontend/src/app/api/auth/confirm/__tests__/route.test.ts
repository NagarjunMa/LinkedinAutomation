import { beforeEach, describe, expect, it, vi } from 'vitest'
import { NextRequest } from 'next/server'

const createServerClientMock = vi.hoisted(() => vi.fn())
const verifyOtpMock = vi.hoisted(() => vi.fn())

vi.mock('@/lib/supabase-server', () => ({
  createServerSupabaseClientWithResponse: createServerClientMock,
}))

describe('email confirmation callback', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.stubEnv('NEXT_PUBLIC_FRONTEND_URL', 'https://www.prismpro.live')
    vi.stubEnv('PRISM_PRO_PUBLIC_PREVIEW_ONLY', 'false')
    createServerClientMock.mockImplementation(async (response) => {
      response.cookies.set('sb-session', 'confirmed-session', { path: '/' })
      return { auth: { verifyOtp: verifyOtpMock } }
    })
  })

  it('does not verify a token while the public preview is active', async () => {
    vi.stubEnv('PRISM_PRO_PUBLIC_PREVIEW_ONLY', 'true')
    const { GET } = await import('@/app/api/auth/confirm/route')

    const response = await GET(
      new NextRequest(
        'https://www.prismpro.live/api/auth/confirm?token_hash=hash&type=email',
      ),
    )

    expect(response.headers.get('location')).toBe('https://www.prismpro.live/')
    expect(response.headers.get('cache-control')).toContain('no-store')
    expect(createServerClientMock).not.toHaveBeenCalled()
    expect(verifyOtpMock).not.toHaveBeenCalled()
  })

  it('preserves confirmation cookies and restricts the redirect destination', async () => {
    verifyOtpMock.mockResolvedValue({
      data: { session: { access_token: 'not-logged' } },
      error: null,
    })
    const { GET } = await import('@/app/api/auth/confirm/route')

    const response = await GET(
      new NextRequest(
        'https://www.prismpro.live/api/auth/confirm?token_hash=hash&type=email&next=//attacker.example',
      ),
    )

    expect(response.headers.get('location')).toBe(
      'https://www.prismpro.live/dashboard',
    )
    expect(response.cookies.get('sb-session')?.value).toBe('confirmed-session')
    expect(response.headers.get('cache-control')).toContain('no-store')
  })

  it('rejects unknown OTP types before calling Supabase', async () => {
    const { GET } = await import('@/app/api/auth/confirm/route')

    const response = await GET(
      new NextRequest(
        'https://www.prismpro.live/api/auth/confirm?token_hash=hash&type=admin',
      ),
    )

    expect(response.headers.get('location')).toBe(
      'https://www.prismpro.live/login?error=invalid_confirmation_link',
    )
    expect(createServerClientMock).not.toHaveBeenCalled()
  })
})
