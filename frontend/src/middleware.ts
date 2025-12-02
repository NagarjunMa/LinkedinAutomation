import { NextResponse, type NextRequest } from 'next/server'

const DASHBOARD_ROOT = '/dashboard'
const ACCESS_COOKIE = 'sb-access-token'
const REFRESH_COOKIE = 'sb-refresh-token'

const hasSupabaseSession = (request: NextRequest) => {
    const hasAccessToken = Boolean(request.cookies.get(ACCESS_COOKIE)?.value)
    const hasRefreshToken = Boolean(request.cookies.get(REFRESH_COOKIE)?.value)

    // Check for any Supabase auth cookie patterns using the correct Next.js cookies API
    let hasAnySupabaseAuth = false
    request.cookies.getAll().forEach(cookie => {
        if (cookie.name.startsWith('sb-') && cookie.value) {
            hasAnySupabaseAuth = true
        }
    })

    return hasAccessToken || hasRefreshToken || hasAnySupabaseAuth
}

export function middleware(request: NextRequest) {
    const pathname = request.nextUrl.pathname
    const loggedIn = hasSupabaseSession(request)

    if (!loggedIn && pathname.startsWith(DASHBOARD_ROOT)) {
        const redirectUrl = new URL('/', request.url)
        return NextResponse.redirect(redirectUrl)
    }

    if (loggedIn && pathname === '/') {
        const redirectUrl = new URL(DASHBOARD_ROOT, request.url)
        return NextResponse.redirect(redirectUrl)
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
