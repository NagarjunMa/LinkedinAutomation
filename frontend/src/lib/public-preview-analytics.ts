export type PublicPreviewFormLocation = 'hero' | 'final_cta'
export type PublicPreviewValidationCategory =
  | 'consent'
  | 'server_validation'
  | 'rate_limit'
  | 'unavailable'

export type PublicPreviewEvent =
  | { event_name: 'hero_cta'; form_location: PublicPreviewFormLocation }
  | { event_name: 'form_start'; form_location: PublicPreviewFormLocation }
  | { event_name: 'form_success'; form_location: PublicPreviewFormLocation }
  | {
      event_name: 'form_validation_failure'
      form_location: PublicPreviewFormLocation
      validation_category: PublicPreviewValidationCategory
    }
  | { event_name: 'scroll_depth'; scroll_depth: 25 | 50 | 75 | 100 }

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export function trackPublicPreviewEvent(event: PublicPreviewEvent): void {
  if (typeof window === 'undefined') return

  void fetch(`${API_BASE_URL}/api/v1/public-preview/events`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(event),
    cache: 'no-store',
    credentials: 'omit',
    keepalive: true,
  }).catch(() => {
    // Analytics is deliberately best-effort and must never interrupt the CTA.
  })
}
