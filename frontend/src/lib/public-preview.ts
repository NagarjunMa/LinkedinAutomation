const PUBLIC_PREVIEW_RESTRICTED_PATHS = [
  '/login',
  '/onboarding',
  '/dashboard',
  '/docs',
  '/api/auth',
] as const

export function isPublicPreviewOnly(): boolean {
  return process.env.PRISM_PRO_PUBLIC_PREVIEW_ONLY !== 'false'
}

export function isPublicPreviewRestrictedPath(pathname: string): boolean {
  return PUBLIC_PREVIEW_RESTRICTED_PATHS.some(
    (path) => pathname === path || pathname.startsWith(`${path}/`),
  )
}
