const LOCAL_APP_ORIGIN = 'http://localhost:3000'

export function normalizeAppOrigin(value?: string | null): string | null {
  const raw = value?.trim()
  if (!raw) return null

  const withProtocol = /^https?:\/\//i.test(raw) ? raw : `https://${raw}`

  try {
    const url = new URL(withProtocol)

    if (url.protocol !== 'http:' && url.protocol !== 'https:') {
      return null
    }

    const path = url.pathname === '/' ? '' : url.pathname.replace(/\/+$/, '')
    return `${url.origin}${path}`
  } catch {
    return null
  }
}

export function getConfiguredAppOrigin(fallback?: string | null): string {
  return (
    normalizeAppOrigin(process.env.NEXT_PUBLIC_FRONTEND_URL) ??
    normalizeAppOrigin(process.env.NEXT_PUBLIC_SITE_URL) ??
    normalizeAppOrigin(fallback) ??
    LOCAL_APP_ORIGIN
  )
}

export function getBrowserAppOrigin(): string {
  const browserOrigin = typeof window !== 'undefined' ? window.location.origin : undefined

  if (process.env.NODE_ENV !== 'production') {
    return normalizeAppOrigin(browserOrigin) ?? getConfiguredAppOrigin(LOCAL_APP_ORIGIN)
  }

  return getConfiguredAppOrigin(browserOrigin)
}
