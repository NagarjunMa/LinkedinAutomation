import { NextRequest, NextResponse } from 'next/server'
import { createServerSupabaseClientWithResponse } from '@/lib/supabase-server'
import { getConfiguredAppOrigin } from '@/lib/url'
import { getSafeAuthRedirectPath } from '@/lib/auth-redirect'
import { isPublicPreviewOnly } from '@/lib/public-preview'

export const runtime = 'nodejs'

function createPrivateRedirect(url: string) {
  const response = NextResponse.redirect(url)
  response.headers.set('Cache-Control', 'private, no-cache, no-store, must-revalidate, max-age=0')
  response.headers.set('Pragma', 'no-cache')
  response.headers.set('Expires', '0')
  return response
}

export async function GET(request: NextRequest) {
  const requestUrl = new URL(request.url)
  const code = requestUrl.searchParams.get('code')
  const oauthError = requestUrl.searchParams.get('error')
  const next = getSafeAuthRedirectPath(requestUrl.searchParams.get('next'))

  // Use configured frontend URL in production, fallback to request origin in dev
  const origin = getConfiguredAppOrigin(requestUrl.origin)

  // Preview mode is deliberately checked before provider errors or code
  // exchange so this route cannot create or refresh a public session.
  if (isPublicPreviewOnly()) {
    return createPrivateRedirect(origin)
  }

  if (oauthError) {
    return createPrivateRedirect(`${origin}/login?error=oauth_failed`)
  }

  if (code) {
    // The response is created before the exchange so refreshed cookies and
    // anti-caching headers survive both success and failure paths.
    const response = createPrivateRedirect(`${origin}/login?error=session_failed`)
    const supabase = await createServerSupabaseClientWithResponse(response)

    try {
      const { data, error } = await supabase.auth.exchangeCodeForSession(code)

      if (!error && data?.session) {
        response.headers.set('Location', new URL(next, origin).toString())
        return response
      }
    } catch {
      response.headers.set('Location', `${origin}/login?error=callback_error`)
    }

    return response
  }

  return createPrivateRedirect(`${origin}/login?error=no_code`)
}
