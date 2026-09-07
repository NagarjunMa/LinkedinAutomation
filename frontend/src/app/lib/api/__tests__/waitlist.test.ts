import { afterEach, describe, expect, it, vi } from 'vitest'

import { submitWaitlist, WaitlistError } from '@/app/lib/api/waitlist'


describe('waitlist API', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('posts a credential-free payload to the public waitlist route', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          message: "You're on the list. We'll be in touch when there is a useful next step.",
        }),
        { status: 202, headers: { 'Content-Type': 'application/json' } },
      ),
    )
    vi.stubGlobal('fetch', fetchMock)

    await submitWaitlist({
      email: 'candidate@example.com',
      consent: true,
    })

    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/waitlist',
      expect.objectContaining({
        method: 'POST',
        credentials: 'omit',
        cache: 'no-store',
      }),
    )
    const options = fetchMock.mock.calls[0][1] as RequestInit
    expect(options.headers).toEqual({ 'Content-Type': 'application/json' })
    expect(options.body).not.toContain('Authorization')
  })

  it.each([
    [422, 'validation'],
    [429, 'rate_limit'],
    [503, 'unavailable'],
  ] as const)('normalizes an HTTP %s failure', async (status, kind) => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{}', { status })))

    await expect(
      submitWaitlist({ email: 'candidate@example.com', consent: true }),
    ).rejects.toMatchObject({ kind } satisfies Partial<WaitlistError>)
  })
})
