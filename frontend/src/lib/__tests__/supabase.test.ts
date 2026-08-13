import { beforeEach, describe, expect, it, vi } from 'vitest'

const createBrowserClientMock = vi.hoisted(() => vi.fn())

vi.mock('@supabase/ssr', () => ({
  createBrowserClient: createBrowserClientMock,
}))

describe('browser Supabase client', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.clearAllMocks()
    vi.stubEnv('NEXT_PUBLIC_SUPABASE_URL', 'https://project.supabase.co')
    vi.stubEnv('NEXT_PUBLIC_SUPABASE_ANON_KEY', 'publishable-key')
    createBrowserClientMock.mockReturnValue({ auth: {} })
  })

  it('delegates PKCE and session persistence to the SSR cookie client', async () => {
    const { createClient } = await import('@/lib/supabase')

    createClient()

    expect(createBrowserClientMock).toHaveBeenCalledWith(
      'https://project.supabase.co',
      'publishable-key',
    )
  })
})
