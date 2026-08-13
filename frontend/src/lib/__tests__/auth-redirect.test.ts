import { describe, expect, it } from 'vitest'

import { getSafeAuthRedirectPath } from '@/lib/auth-redirect'

describe('getSafeAuthRedirectPath', () => {
  it.each([
    [null, '/dashboard'],
    ['https://attacker.example/steal', '/dashboard'],
    ['//attacker.example/steal', '/dashboard'],
    ['/\\attacker.example/steal', '/dashboard'],
    ['/api/auth/callback', '/dashboard'],
  ])('rejects unsafe destination %s', (value, expected) => {
    expect(getSafeAuthRedirectPath(value)).toBe(expected)
  })

  it('keeps allowlisted authenticated paths and query parameters', () => {
    expect(getSafeAuthRedirectPath('/dashboard/resume?tab=versions')).toBe(
      '/dashboard/resume?tab=versions',
    )
    expect(getSafeAuthRedirectPath('/onboarding')).toBe('/onboarding')
  })
})
