import { createServerClient } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'

// Simple in-memory cache for session validation
// Cache sessions for 5 minutes to reduce auth overhead
const sessionCache = new Map<string, { session: any, timestamp: number }>()
const CACHE_DURATION = 5 * 60 * 1000 // 5 minutes

function getSessionKey(request: NextRequest): string {
    // Create cache key from access token and refresh token
    const accessToken = request.cookies.get('sb-access-token')?.value
    const refreshToken = request.cookies.get('sb-refresh-token')?.value
    return `${accessToken}-${refreshToken}`
}

function getCachedSession(key: string) {
    const cached = sessionCache.get(key)
    if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
        return cached.session
    }
    return null
}

function setCachedSession(key: string, session: any) {
    sessionCache.set(key, { session, timestamp: Date.now() })

    // Cleanup old entries to prevent memory leaks
    if (sessionCache.size > 100) {
        const cutoff = Date.now() - CACHE_DURATION
        for (const [k, v] of sessionCache.entries()) {
            if (v.timestamp < cutoff) {
                sessionCache.delete(k)
            }
        }
    }
}

export async function middleware(request: NextRequest) {

    let supabaseResponse = NextResponse.next({
        request,
    })

    // Check cache first for session validation
    const sessionKey = getSessionKey(request)
    let session = getCachedSession(sessionKey)

    if (!session) {
        const supabase = createServerClient(
            process.env.NEXT_PUBLIC_SUPABASE_URL!,
            process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
            {
                cookies: {
                    getAll() {
                        return request.cookies.getAll()
                    },
                    setAll(cookiesToSet) {
                        cookiesToSet.forEach(({ name, value, options }) => {
                            request.cookies.set(name, value)
                            supabaseResponse = NextResponse.next({
                                request,
                            })
                            supabaseResponse.cookies.set(name, value, options)
                        })
                    },
                },
            }
        )

        // Only call getSession if not cached
        const {
            data: { session: freshSession },
        } = await supabase.auth.getSession()

        session = freshSession
        setCachedSession(sessionKey, session)
    }


    // If no session and trying to access protected routes, redirect to landing
    if (!session && request.nextUrl.pathname.startsWith('/dashboard')) {
        return NextResponse.redirect(new URL('/', request.url))
    }

    // If no session and trying to access onboarding, redirect to landing
    if (!session && request.nextUrl.pathname === '/onboarding') {
        return NextResponse.redirect(new URL('/', request.url))
    }

    // Temporarily comment out this redirect to allow access to landing page
    // If session exists and trying to access landing page, redirect to dashboard
    // if (session && request.nextUrl.pathname === '/') {
    //     console.log('Middleware: Redirecting to dashboard from landing page')
    //     return NextResponse.redirect(new URL('/dashboard', request.url))
    // }

    // If user has completed onboarding and tries to access onboarding page, redirect to dashboard
    if (session && request.nextUrl.pathname === '/onboarding') {
        const user = session.user
        const hasCompletedOnboarding = user.user_metadata?.onboarding_completed
        const hasOAuthProvider = user.user_metadata?.oauth_provider

        // Only redirect if user has completed both onboarding and OAuth
        if (hasCompletedOnboarding && hasOAuthProvider) {
            return NextResponse.redirect(new URL('/dashboard', request.url))
        }
    }

    return supabaseResponse
}

export const config = {
    matcher: [
        /*
         * Match all request paths except for the ones starting with:
         * - _next/static (static files)
         * - _next/image (image optimization files)
         * - favicon.ico (favicon file)
         * - public folder
         */
        '/((?!_next/static|_next/image|favicon.ico|public).*)',
    ],
}
