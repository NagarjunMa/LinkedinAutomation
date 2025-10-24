import { createServerClient } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'

export async function middleware(request: NextRequest) {
    let supabaseResponse = NextResponse.next({
        request,
    })

    const supabase = createServerClient(
        process.env.NEXT_PUBLIC_SUPABASE_URL!,
        process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
        {
            cookies: {
                get(name: string) {
                    return request.cookies.get(name)?.value
                },
                set(name: string, value: string, options: any) {
                    request.cookies.set(name, value)
                    supabaseResponse = NextResponse.next({
                        request,
                    })
                    supabaseResponse.cookies.set(name, value, options)
                },
                remove(name: string, options: any) {
                    request.cookies.delete(name)
                    supabaseResponse = NextResponse.next({
                        request,
                    })
                    supabaseResponse.cookies.delete(name)
                },
            },
        }
    )

    // Refresh session if expired
    const {
        data: { session },
    } = await supabase.auth.getSession()

    // If no session and trying to access protected routes, redirect to landing
    if (!session && request.nextUrl.pathname.startsWith('/dashboard')) {
        return NextResponse.redirect(new URL('/', request.url))
    }

    // If session exists and trying to access landing page, redirect to dashboard
    if (session && request.nextUrl.pathname === '/') {
        return NextResponse.redirect(new URL('/dashboard', request.url))
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
