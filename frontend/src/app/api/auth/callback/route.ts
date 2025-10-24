import { createServerClient } from '@supabase/ssr'
import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'

export async function GET(request: NextRequest) {
  const { searchParams, origin } = new URL(request.url)
  const code = searchParams.get('code')
  const error_param = searchParams.get('error')
  const next = searchParams.get('next') ?? '/dashboard'

  console.log('Auth callback received:', { code: !!code, error_param, origin })

  // Check for OAuth error first
  if (error_param) {
    console.error('OAuth error from provider:', error_param)
    return NextResponse.redirect(`${origin}/login?error=${error_param}`)
  }

  if (code) {
    const cookieStore = cookies()
    const supabase = createServerClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
      {
        cookies: {
          get(name: string) {
            return cookieStore.get(name)?.value
          },
          set(name: string, value: string, options: any) {
            cookieStore.set(name, value, options)
          },
          remove(name: string, options: any) {
            cookieStore.delete(name)
          },
        },
      }
    )

    try {
      const { data, error } = await supabase.auth.exchangeCodeForSession(code)

      console.log('Session exchange result:', {
        hasSession: !!data?.session,
        hasUser: !!data?.user,
        error: error?.message
      })

      if (!error && data?.session) {
        const forwardedHost = request.headers.get('x-forwarded-host')
        const isLocalEnv = process.env.NODE_ENV === 'development'

        // Set the session cookies
        const response = NextResponse.redirect(
          isLocalEnv
            ? `${origin}${next}`
            : forwardedHost
              ? `https://${forwardedHost}${next}`
              : `${origin}${next}`
        )

        return response
      } else {
        console.error('Auth exchange failed:', error?.message || 'No session created')
        return NextResponse.redirect(`${origin}/login?error=session_failed&details=${encodeURIComponent(error?.message || 'No session')}`)
      }
    } catch (err) {
      console.error('Auth callback error:', err)
      return NextResponse.redirect(`${origin}/login?error=callback_error`)
    }
  }

  // No code parameter
  console.error('No authorization code received')
  return NextResponse.redirect(`${origin}/login?error=no_code`)
}
