import { NextRequest, NextResponse } from 'next/server'
import { createServerSupabaseClientWithResponse } from '@/lib/supabase-server'
import { getSafeAuthRedirectPath } from '@/lib/auth-redirect'
import { getConfiguredAppOrigin } from '@/lib/url'

export const runtime = 'nodejs'

const OTP_TYPES = new Set(['email', 'recovery', 'signup', 'magiclink'] as const)

type OtpType = 'email' | 'recovery' | 'signup' | 'magiclink'

function createPrivateRedirect(url: string) {
  const response = NextResponse.redirect(url)
  response.headers.set('Cache-Control', 'private, no-cache, no-store, must-revalidate, max-age=0')
  response.headers.set('Pragma', 'no-cache')
  response.headers.set('Expires', '0')
  return response
}

export async function GET(request: NextRequest) {
  const requestUrl = new URL(request.url)
  const { searchParams } = requestUrl
  const token_hash = searchParams.get('token_hash')
  const type = searchParams.get('type')
  const next = getSafeAuthRedirectPath(searchParams.get('next'))
  const origin = getConfiguredAppOrigin(requestUrl.origin)

  if (!token_hash || !type || !OTP_TYPES.has(type as OtpType)) {
    return createPrivateRedirect(`${origin}/login?error=invalid_confirmation_link`)
  }

  const response = createPrivateRedirect(`${origin}/login?error=confirmation_failed`)
  const supabase = await createServerSupabaseClientWithResponse(response)

  try {
    const { data, error } = await supabase.auth.verifyOtp({
      token_hash,
      type: type as OtpType,
    })

    if (!error && data.session) {
      response.headers.set('Location', new URL(next, origin).toString())
    }
  } catch {
    response.headers.set('Location', `${origin}/login?error=confirmation_error`)
  }

  return response
}
