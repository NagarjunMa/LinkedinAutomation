import { NextRequest, NextResponse } from 'next/server'
import { createServerSupabaseClientWithResponse } from '@/lib/supabase-server'

export const runtime = 'nodejs'

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
    // Create response early to properly set cookies
    const response = NextResponse.redirect(`${origin}${next}`)

    // Create Supabase client with response cookie handling
    const supabase = createServerSupabaseClientWithResponse(response)

    try {
      const { data, error } = await supabase.auth.exchangeCodeForSession(code)

      console.log('Session exchange result:', {
        hasSession: !!data?.session,
        hasUser: !!data?.user,
        error: error?.message
      })

      if (!error && data?.session) {

        // If user has Gmail scope, also notify backend about OAuth connection
        try {
          const user = data.session.user
          if (user && data.session.provider_token) {
            // Send OAuth data to backend for Gmail integration
            const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
            await fetch(`${backendUrl}/api/v1/email-agent/oauth/callback`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${data.session.access_token}`
              },
              body: JSON.stringify({
                user_id: user.id,
                provider_token: data.session.provider_token,
                provider_refresh_token: data.session.provider_refresh_token,
                email: user.email
              })
            }).catch(err => {
              console.warn('Failed to sync OAuth with backend:', err)
              // Don't fail the auth flow if backend sync fails
            })
          }
        } catch (err) {
          console.warn('Backend OAuth sync failed:', err)
        }

        console.log('Session exchange successful:', {
          userId: data.session.user.id,
          accessToken: !!data.session.access_token,
          refreshToken: !!data.session.refresh_token,
          expiresAt: data.session.expires_at
        })

        // Force a small delay to ensure cookies are set
        await new Promise(resolve => setTimeout(resolve, 100))

        // Add cache-control headers to prevent caching issues
        response.headers.set('Cache-Control', 'no-cache, no-store, must-revalidate')
        response.headers.set('Pragma', 'no-cache')
        response.headers.set('Expires', '0')

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
