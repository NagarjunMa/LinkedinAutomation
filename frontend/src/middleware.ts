import { NextResponse, type NextRequest } from 'next/server'

const DASHBOARD_ROOT = '/dashboard'
const ACCESS_COOKIE = 'sb-access-token'
const REFRESH_COOKIE = 'sb-refresh-token'

const hasSupabaseSession = (request: NextRequest) => {
    // Get Supabase project reference from environment
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
    const projectRef = supabaseUrl ? new URL(supabaseUrl).hostname.split('.')[0] : 'fecoflibopgxliexcdbg'

    // Check for Supabase auth token cookies (they can be chunked)
    const authCookiePattern = `sb-${projectRef}-auth-token`

    let hasValidAuthCookie = false
    const foundCookies: string[] = []

    request.cookies.getAll().forEach(cookie => {
        // Check for main auth token cookie or chunked versions
        if (cookie.name === authCookiePattern || cookie.name.startsWith(`${authCookiePattern}.`)) {
            foundCookies.push(cookie.name)
            // Validate cookie value - should contain JSON-like structure for access_token
            if (cookie.value &&
                cookie.value.length > 10 &&
                (cookie.value.includes('access_token') ||
                    cookie.value.includes('refresh_token') ||
                    cookie.value.startsWith('base64-'))) {
                hasValidAuthCookie = true
            }
        }
    })

    // Also check for legacy cookie names as fallback
    const hasLegacyAuth = Boolean(
        request.cookies.get('sb-access-token')?.value ||
        request.cookies.get('sb-refresh-token')?.value ||
        request.cookies.get(ACCESS_COOKIE)?.value ||
        request.cookies.get(REFRESH_COOKIE)?.value
    )

    // Logs removed

    return hasValidAuthCookie || hasLegacyAuth
}

export function middleware(request: NextRequest) {
    const pathname = request.nextUrl.pathname

    // Test bypass: allow Playwright e2e to access protected routes without auth.
    // Cookie-based because Next.js Edge runtime does not expose runtime env vars.
    // Gated to non-production environments so the bypass is never live on prod.
    if (
        process.env.NODE_ENV !== 'production' &&
        request.cookies.get('test-bypass-auth')?.value === '1'
    ) {
        return NextResponse.next()
    }

    // Skip auth middleware for auth-related routes and API routes
    if (pathname.startsWith('/api/auth') ||
        pathname.startsWith('/login') ||
        pathname.startsWith('/signup') ||
        pathname.startsWith('/reset-password')) {
        return NextResponse.next()
    }

    // Special handling for potential auth callback scenarios
    const searchParams = request.nextUrl.searchParams
    const hasAuthCode = searchParams.has('code')
    const hasTokenHash = searchParams.has('token_hash')
    const isAuthCallback = hasAuthCode || hasTokenHash

    // If this looks like an auth callback, be more lenient with timing
    if (isAuthCallback && pathname.startsWith(DASHBOARD_ROOT)) {
        if (process.env.NODE_ENV === 'development') {
            console.log(`🔄 Middleware: Potential auth callback detected on ${pathname}, allowing through temporarily`)
        }
        // Allow the request to proceed - let the auth context handle the session loading
        return NextResponse.next()
    }

    const loggedIn = hasSupabaseSession(request)

    // Logs removed

    if (!loggedIn && pathname.startsWith(DASHBOARD_ROOT)) {
        const redirectUrl = new URL('/', request.url)
        const response = NextResponse.redirect(redirectUrl)
        // Prevent caching of the redirect response
        response.headers.set('Cache-Control', 'no-cache, no-store, must-revalidate')
        response.headers.set('Pragma', 'no-cache')
        response.headers.set('Expires', '0')
        return response
    }

    if (loggedIn && pathname === '/') {
        const redirectUrl = new URL(DASHBOARD_ROOT, request.url)
        const response = NextResponse.redirect(redirectUrl)
        response.headers.set('Cache-Control', 'no-cache, no-store, must-revalidate')
        return response
    }

    return NextResponse.next()
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
