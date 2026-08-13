const AUTHENTICATED_PATH_PREFIXES = ['/dashboard', '/onboarding'] as const

export function getSafeAuthRedirectPath(value: string | null) {
  if (!value || !value.startsWith('/') || value.startsWith('//') || value.includes('\\')) {
    return '/dashboard'
  }

  try {
    const parsed = new URL(value, 'https://auth-redirect.local')
    const isAllowed = AUTHENTICATED_PATH_PREFIXES.some(
      (prefix) => parsed.pathname === prefix || parsed.pathname.startsWith(`${prefix}/`),
    )

    return isAllowed ? `${parsed.pathname}${parsed.search}` : '/dashboard'
  } catch {
    return '/dashboard'
  }
}
