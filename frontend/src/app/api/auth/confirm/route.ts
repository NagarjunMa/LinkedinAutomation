import { NextRequest, NextResponse } from 'next/server'
import { createServerSupabaseClientWithResponse } from '@/lib/supabase-server'

export const runtime = 'nodejs'

export async function GET(request: NextRequest) {
  const { searchParams, origin } = new URL(request.url)
  const token_hash = searchParams.get('token_hash')
  const type = searchParams.get('type')
  const next = searchParams.get('next') ?? '/dashboard'

  console.log('Email confirmation received:', {
    hasTokenHash: !!token_hash,
    type,
    origin
  })

  // Validate required parameters
  if (!token_hash || !type) {
    console.error('Missing token_hash or type parameter')
    return NextResponse.redirect(`${origin}/login?error=invalid_confirmation_link`)
  }

  // Create response early to properly set cookies
  const response = NextResponse.redirect(`${origin}${next}`)

  // Create Supabase client with response cookie handling
  const supabase = createServerSupabaseClientWithResponse(response)

  try {
    const { data, error } = await supabase.auth.verifyOtp({
      token_hash,
      type: type as 'email' | 'recovery' | 'signup' | 'magiclink'
    })

    console.log('Email confirmation result:', {
      hasSession: !!data?.session,
      hasUser: !!data?.user,
      error: error?.message
    })

    if (error) {
      console.error('Email confirmation failed:', error.message)
      return NextResponse.redirect(
        `${origin}/login?error=confirmation_failed&details=${encodeURIComponent(error.message)}`
      )
    }

    if (!data.session) {
      console.error('No session created after email confirmation')
      return NextResponse.redirect(
        `${origin}/login?error=no_session&message=Please try signing in again`
      )
    }

    // Force a small delay to ensure cookies are set
    await new Promise(resolve => setTimeout(resolve, 100))

    console.log('Email confirmation successful:', {
      userId: data.session.user.id,
      email: data.session.user.email
    })

    // Add cache-control headers to prevent caching issues
    response.headers.set('Cache-Control', 'no-cache, no-store, must-revalidate')
    response.headers.set('Pragma', 'no-cache')
    response.headers.set('Expires', '0')

    return response

  } catch (err) {
    console.error('Email confirmation error:', err)
    return NextResponse.redirect(
      `${origin}/login?error=confirmation_error&message=Something went wrong`
    )
  }
}