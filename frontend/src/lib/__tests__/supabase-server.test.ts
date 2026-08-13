import { beforeEach, describe, expect, it, vi } from 'vitest'
import { NextResponse } from 'next/server'

const createServerClientMock = vi.hoisted(() => vi.fn())
const cookieStore = vi.hoisted(() => ({
  getAll: vi.fn(() => []),
  set: vi.fn(),
}))

vi.mock('@supabase/ssr', () => ({
  createServerClient: createServerClientMock,
}))

vi.mock('next/headers', () => ({
  cookies: vi.fn(async () => cookieStore),
}))

describe('server Supabase client', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.clearAllMocks()
    vi.stubEnv('NEXT_PUBLIC_SUPABASE_URL', 'https://project.supabase.co')
    vi.stubEnv('NEXT_PUBLIC_SUPABASE_ANON_KEY', 'publishable-key')
    createServerClientMock.mockReturnValue({ auth: {} })
  })

  it('writes auth cookies and every SSR anti-cache header to the response', async () => {
    const response = NextResponse.next()
    const { createServerSupabaseClientWithResponse } = await import(
      '@/lib/supabase-server'
    )

    await createServerSupabaseClientWithResponse(response)
    const options = createServerClientMock.mock.calls[0][2]
    options.cookies.setAll(
      [{ name: 'sb-session', value: 'fresh', options: { path: '/' } }],
      {
        'Cache-Control': 'private, no-store',
        Expires: '0',
        Pragma: 'no-cache',
      },
    )

    expect(response.cookies.get('sb-session')?.value).toBe('fresh')
    expect(response.headers.get('cache-control')).toBe('private, no-store')
    expect(response.headers.get('expires')).toBe('0')
    expect(response.headers.get('pragma')).toBe('no-cache')
  })
})
