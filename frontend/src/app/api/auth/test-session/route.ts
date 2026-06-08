import { NextRequest, NextResponse } from 'next/server'
import { createServerSupabaseClient } from '@/lib/supabase-server'

export const runtime = 'nodejs'

/**
 * Debug endpoint to test session state and cookie detection
 * GET /api/auth/test-session
 */
export async function GET(request: NextRequest) {
  try {
    const supabase = await createServerSupabaseClient()
    const { data: { session }, error } = await supabase.auth.getSession()

    // Get all cookies for debugging
    const allCookies = request.cookies.getAll()
    const authCookies = allCookies.filter(c =>
      c.name.includes('sb-') ||
      c.name.includes('auth') ||
      c.name.includes('access') ||
      c.name.includes('refresh')
    )

    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
    const projectRef = supabaseUrl ? new URL(supabaseUrl).hostname.split('.')[0] : 'fecoflibopgxliexcdbg'
    const expectedAuthCookie = `sb-${projectRef}-auth-token`

    const debugInfo = {
      timestamp: new Date().toISOString(),
      hasSession: !!session,
      sessionDetails: session ? {
        userId: session.user.id,
        email: session.user.email,
        expiresAt: session.expires_at,
        hasAccessToken: !!session.access_token
      } : null,
      error: error?.message,
      cookieAnalysis: {
        totalCookies: allCookies.length,
        authCookiesFound: authCookies.length,
        authCookieNames: authCookies.map(c => c.name),
        expectedAuthCookie,
        hasExpectedCookie: authCookies.some(c => c.name === expectedAuthCookie || c.name.startsWith(`${expectedAuthCookie}.`)),
      },
      projectRef,
      environment: process.env.NODE_ENV,
      url: request.url
    }

    return NextResponse.json(debugInfo, {
      status: 200,
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate'
      }
    })

  } catch (error) {
    console.error('Session test error:', error)
    return NextResponse.json({
      error: 'Failed to test session',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}

export const dynamic = 'force-dynamic'
