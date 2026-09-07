export const CAREER_STAGES = [
  { value: 'student', label: 'Student' },
  { value: 'new_graduate', label: 'New graduate' },
  { value: 'early_career', label: 'Early-career engineer' },
  { value: 'experienced_ic', label: 'Experienced individual contributor' },
  { value: 'technical_leader', label: 'Technical leader' },
  { value: 'career_switcher', label: 'Career switcher' },
  { value: 'returning_professional', label: 'Returning professional' },
] as const

export type CareerStage = (typeof CAREER_STAGES)[number]['value']

export interface WaitlistSubmission {
  email: string
  career_stage?: CareerStage
  target_role?: string
  communication_challenge?: string
  consent: true
  company_website?: string
}

interface WaitlistResponse {
  message: string
}

export class WaitlistError extends Error {
  constructor(
    message: string,
    public readonly kind: 'validation' | 'rate_limit' | 'unavailable',
  ) {
    super(message)
    this.name = 'WaitlistError'
  }
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function submitWaitlist(
  submission: WaitlistSubmission,
): Promise<WaitlistResponse> {
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), 10_000)

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/waitlist`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(submission),
      cache: 'no-store',
      credentials: 'omit',
      signal: controller.signal,
    })

    if (response.status === 422) {
      throw new WaitlistError(
        'Check your email and the highlighted fields, then try again.',
        'validation',
      )
    }
    if (response.status === 429) {
      throw new WaitlistError(
        'Too many attempts. Please wait a minute and try again.',
        'rate_limit',
      )
    }
    if (!response.ok) {
      throw new WaitlistError(
        'The waitlist is temporarily unavailable. Please try again later.',
        'unavailable',
      )
    }

    return (await response.json()) as WaitlistResponse
  } catch (error) {
    if (error instanceof WaitlistError) {
      throw error
    }
    throw new WaitlistError(
      'We could not reach the waitlist. Check your connection and try again.',
      'unavailable',
    )
  } finally {
    window.clearTimeout(timeout)
  }
}
