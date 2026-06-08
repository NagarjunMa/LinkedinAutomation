import { createServerClient } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'

export async function middleware(request: NextRequest) {
    if (
        process.env.NODE_ENV !== 'production' &&
        request.cookies.get('test-bypass-auth')?.value === '1'
    ) {
        return NextResponse.next()
    }

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
                        supabaseResponse = NextResponse.next({ request })
                        supabaseResponse.cookies.set(name, value, options)
                    })
                },
            },
        }
    )

    const {
        data: { user },
    } = await supabase.auth.getUser()

    if (!user && request.nextUrl.pathname.startsWith('/dashboard')) {
        return NextResponse.redirect(new URL('/', request.url))
    }

    if (!user && request.nextUrl.pathname === '/onboarding') {
        return NextResponse.redirect(new URL('/', request.url))
    }

    if (user && request.nextUrl.pathname === '/onboarding') {
        const hasCompletedOnboarding = user.user_metadata?.onboarding_completed
        const hasOAuthProvider = user.user_metadata?.oauth_provider

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
