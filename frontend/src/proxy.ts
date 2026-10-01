import type { NextRequest } from 'next/server'

import { updateSession } from '@/lib/supabase-proxy'
import { buildContentSecurityPolicy } from '@/lib/security-csp'

export async function proxy(request: NextRequest) {
  const nonce = Buffer.from(crypto.randomUUID()).toString('base64')
  const policy = buildContentSecurityPolicy(nonce)
  request.headers.set('x-nonce', nonce)
  request.headers.set('Content-Security-Policy', policy)

  const response = await updateSession(request)
  response.headers.set('Content-Security-Policy', policy)
  return response
}

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
}
