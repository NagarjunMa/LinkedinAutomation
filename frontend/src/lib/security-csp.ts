/** Build the browser policy for one HTML request. Inline React styles remain
 * allowed; executable inline scripts require this request's nonce. */
export function buildContentSecurityPolicy(nonce: string): string {
  const isProduction = process.env.NODE_ENV === 'production'
  const apiOrigin = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  const supabaseOrigin = process.env.NEXT_PUBLIC_SUPABASE_URL

  return [
    "default-src 'self'",
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'${isProduction ? '' : " 'unsafe-eval'"}`,
    "script-src-attr 'none'",
    "style-src 'self' 'unsafe-inline'",
    "font-src 'self' data:",
    `img-src 'self' data: blob: https:${isProduction ? '' : ' http:'}`,
    `connect-src 'self' ${[apiOrigin, supabaseOrigin, 'https://*.supabase.co', 'https://accounts.google.com'].filter(Boolean).join(' ')}`,
    "frame-src 'self' blob: https://www.google.com",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
    ...(isProduction ? ["upgrade-insecure-requests"] : []),
  ].join('; ')
}
