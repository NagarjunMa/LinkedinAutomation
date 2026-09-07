import { createServerClient } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'

import {
  isPublicPreviewOnly,
  isPublicPreviewRestrictedPath,
} from '@/lib/public-preview'

const PRIVATE_RESPONSE_HEADERS = {
  'Cache-Control': 'private, no-cache, no-store, must-revalidate, max-age=0',
  Expires: '0',
  Pragma: 'no-cache',
} as const

function applyHeaders(response: NextResponse, headers: Record<string, string>) {
  Object.entries(headers).forEach(([name, value]) => {
    response.headers.set(name, value)
  })
}

function redirectWithAuthState(url: URL, authResponse: NextResponse) {
  const response = NextResponse.redirect(url)

  authResponse.cookies.getAll().forEach((cookie) => {
    response.cookies.set(cookie)
  })
  applyHeaders(response, PRIVATE_RESPONSE_HEADERS)

  return response
}

function redirectToPublicPreview(request: NextRequest) {
  const response = NextResponse.redirect(new URL('/', request.url))
  applyHeaders(response, PRIVATE_RESPONSE_HEADERS)
  return response
}

export async function updateSession(request: NextRequest) {
  const pathname = request.nextUrl.pathname
  const publicPreviewOnly = isPublicPreviewOnly()

  if (publicPreviewOnly && isPublicPreviewRestrictedPath(pathname)) {
    return redirectToPublicPreview(request)
  }

  // Public marketing and legal routes do not need Supabase. Avoid refreshing
  // old sessions or requiring auth configuration on the trailer deployment.
  if (publicPreviewOnly) {
    return NextResponse.next()
  }

  if (
    process.env.NODE_ENV !== 'production' &&
    request.cookies.get('test-bypass-auth')?.value === '1'
  ) {
    return NextResponse.next()
  }

  let supabaseResponse = NextResponse.next({ request })

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll()
        },
        setAll(cookiesToSet, headers) {
          cookiesToSet.forEach(({ name, value }) => {
            request.cookies.set(name, value)
          })

          supabaseResponse = NextResponse.next({ request })
          cookiesToSet.forEach(({ name, value, options }) => {
            supabaseResponse.cookies.set(name, value, options)
          })
          applyHeaders(supabaseResponse, headers)
        },
      },
    },
  )

  let claims: Record<string, unknown> | null = null
  try {
    const { data, error } = await supabase.auth.getClaims()
    claims = error ? null : (data?.claims ?? null)
  } catch {
    // Treat verification outages as unauthenticated. Protected routes fail
    // closed while public routes remain available.
  }
  const userId = typeof claims?.sub === 'string' ? claims.sub : null
  const userMetadata = claims?.user_metadata
  const metadata =
    userMetadata && typeof userMetadata === 'object'
      ? (userMetadata as Record<string, unknown>)
      : null

  if (!userId && pathname.startsWith('/dashboard')) {
    return redirectWithAuthState(new URL('/', request.url), supabaseResponse)
  }

  if (!userId && pathname === '/onboarding') {
    return redirectWithAuthState(new URL('/', request.url), supabaseResponse)
  }

  if (
    userId &&
    pathname === '/onboarding' &&
    metadata?.onboarding_completed &&
    metadata?.oauth_provider
  ) {
    return redirectWithAuthState(new URL('/dashboard', request.url), supabaseResponse)
  }

  return supabaseResponse
}
