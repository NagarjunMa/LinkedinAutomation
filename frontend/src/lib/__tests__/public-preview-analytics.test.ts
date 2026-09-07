import { afterEach, describe, expect, it, vi } from 'vitest'

import { trackPublicPreviewEvent } from '@/lib/public-preview-analytics'


describe('public-preview analytics', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('sends only the approved event dimensions without credentials', () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }))
    vi.stubGlobal('fetch', fetchMock)

    trackPublicPreviewEvent({
      event_name: 'form_validation_failure',
      form_location: 'hero',
      validation_category: 'consent',
    })

    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/public-preview/events',
      expect.objectContaining({
        method: 'POST',
        credentials: 'omit',
        keepalive: true,
      }),
    )
    const options = fetchMock.mock.calls[0][1] as RequestInit
    expect(JSON.parse(String(options.body))).toEqual({
      event_name: 'form_validation_failure',
      form_location: 'hero',
      validation_category: 'consent',
    })
  })
})
