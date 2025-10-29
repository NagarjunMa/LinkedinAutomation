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

    // Refresh session if expired
    const {
        data: { session },
    } = await supabase.auth.getSession()


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
