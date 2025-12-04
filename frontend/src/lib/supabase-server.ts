import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'

// Supabase configuration
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

// Server client for server-side operations
export const createServerSupabaseClient = () => {
  const cookieStore = cookies()

  return createServerClient(supabaseUrl, supabaseAnonKey, {
    cookies: {
      getAll() {
        return cookieStore.getAll()
      },
      setAll(cookiesToSet) {
        try {
          cookiesToSet.forEach(({ name, value, options }) =>
            cookieStore.set(name, value, {
              ...options,
              httpOnly: false, // Allow client-side access
              secure: process.env.NODE_ENV === 'production',
              sameSite: 'lax',
            })
          )
        } catch (error) {
          console.warn('Failed to set server cookies:', error)
          // The `setAll` method was called from a Server Component.
          // This can be ignored if you have middleware refreshing
          // user sessions.
        }
      },
    },
  })
}

// Server client with response cookie handling for API routes
export const createServerSupabaseClientWithResponse = (response: Response) => {
  const cookieStore = cookies()

  return createServerClient(supabaseUrl, supabaseAnonKey, {
    cookies: {
      getAll() {
        return cookieStore.getAll()
      },
      setAll(cookiesToSet) {
        try {
          cookiesToSet.forEach(({ name, value, options }) => {
            // Set in cookie store
            cookieStore.set(name, value, options)

            // Also set in response headers
            const cookieOptions = {
              ...options,
              httpOnly: false,
              secure: process.env.NODE_ENV === 'production',
              sameSite: 'lax',
            }

            const cookieString = `${name}=${value}; ${Object.entries(cookieOptions || {})
              .map(([key, val]) => {
                if (key === 'maxAge') return `Max-Age=${val}`
                if (key === 'sameSite') return `SameSite=${val}`
                if (key === 'httpOnly') return val ? 'HttpOnly' : ''
                if (key === 'secure') return val ? 'Secure' : ''
                if (key === 'path') return `Path=${val}`
                return `${key}=${val}`
              })
              .filter(Boolean)
              .join('; ')}`

            response.headers.append('Set-Cookie', cookieString)
          })
        } catch (error) {
          console.warn('Failed to set response cookies:', error)
        }
      },
    },
  })
}

// Server-side auth utilities
export const getServerSession = async () => {
  try {
    const supabase = createServerSupabaseClient()
    const { data: { session }, error } = await supabase.auth.getSession()

    if (error) {
      console.warn('getServerSession error:', error.message)
      // Don't throw on certain recoverable errors
      if (error.message?.includes('Invalid Refresh Token') ||
          error.message?.includes('refresh_token_not_found')) {
        console.log('Server session expired or invalid, returning null')
        return null
      }
      throw error
    }

    return session
  } catch (error) {
    console.error('getServerSession failed:', error)
    throw error
  }
}

export const getServerUser = async () => {
  const supabase = createServerSupabaseClient()
  const { data: { user }, error } = await supabase.auth.getUser()
  if (error) throw error
  return user
}

// Verify OTP for email verification
export const verifyOtp = async (tokenHash: string, type: string) => {
  const supabase = createServerSupabaseClient()
  const { data, error } = await supabase.auth.verifyOtp({
    token_hash: tokenHash,
    type: type as any
  })
  if (error) throw error
  return data
}
