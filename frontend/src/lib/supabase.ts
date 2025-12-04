import { createBrowserClient } from '@supabase/ssr'

// Supabase configuration
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

// Browser client for client-side operations
export const createClient = () => {
  return createBrowserClient(supabaseUrl, supabaseAnonKey, {
    auth: {
      flowType: 'pkce',
      autoRefreshToken: true,
      persistSession: true,
      detectSessionInUrl: true,
      debug: process.env.NODE_ENV === 'development'
    },
    cookies: {
      get(name: string) {
        if (typeof window === 'undefined') return undefined
        try {
          const cookies = document.cookie.split(';')
          const cookie = cookies.find(c => c.trim().startsWith(`${name}=`))
          const value = cookie ? decodeURIComponent(cookie.split('=')[1]) : undefined
          if (process.env.NODE_ENV === 'development' && name.includes('code_verifier')) {
            console.log(`🍪 Getting cookie ${name}:`, value ? 'found' : 'not found')
          }
          return value
        } catch (error) {
          console.warn(`Failed to get cookie ${name}:`, error)
          return undefined
        }
      },
      set(name: string, value: string, options: Record<string, string | number | boolean>) {
        if (typeof window === 'undefined') return
        try {
          const secureOptions = {
            ...options,
            secure: window.location.protocol === 'https:',
            sameSite: 'lax',
            path: '/'
          }

          const optionsString = Object.entries(secureOptions || {})
            .map(([key, val]) => {
              if (key === 'maxAge') return `max-age=${val}`
              if (key === 'sameSite') return `samesite=${val}`
              if (typeof val === 'boolean') return val ? key : ''
              return `${key}=${val}`
            })
            .filter(Boolean)
            .join('; ')

          const cookieString = `${name}=${encodeURIComponent(value)}; ${optionsString}`
          document.cookie = cookieString

          if (process.env.NODE_ENV === 'development' && name.includes('code_verifier')) {
            console.log(`🍪 Setting cookie ${name}:`, cookieString)
          }
        } catch (error) {
          console.warn(`Failed to set cookie ${name}:`, error)
        }
      },
      remove(name: string, options?: any) {
        if (typeof window === 'undefined') return
        try {
          const removeOptions = {
            ...options,
            path: '/'
          }
          document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; ${Object.entries(removeOptions)
            .map(([key, val]) => `${key}=${val}`)
            .join('; ')}`

          if (process.env.NODE_ENV === 'development') {
            console.log(`🍪 Removing cookie ${name}`)
          }
        } catch (error) {
          console.warn(`Failed to remove cookie ${name}:`, error)
        }
      }
    }
  })
}

// Auth utilities for client-side use
export const signInWithGoogle = async () => {
  const supabase = createClient()

  try {
    // Use signInWithOAuth with proper PKCE handling
    const { data, error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${window.location.origin}/api/auth/callback`,
        skipBrowserRedirect: false,
        queryParams: {
          access_type: 'offline',
          prompt: 'select_account',
          scope: 'email profile https://www.googleapis.com/auth/gmail.readonly'
        }
      }
    })

    if (error) {
      console.error('OAuth initiation error:', error)
      throw error
    }

    console.log('OAuth initiated successfully:', { url: data.url })
    return data
  } catch (error) {
    console.error('signInWithGoogle failed:', error)
    throw error
  }
}

export const signOut = async () => {
  const supabase = createClient()
  const { error } = await supabase.auth.signOut()
  if (error) throw error
}

export const getCurrentUser = async () => {
  const supabase = createClient()
  const { data: { user }, error } = await supabase.auth.getUser()
  if (error) throw error
  return user
}

export const getSession = async () => {
  const supabase = createClient()

  try {
    const { data: { session }, error } = await supabase.auth.getSession()

    if (error) {
      console.warn('getSession error:', error.message)
      // Don't throw on certain recoverable errors
      if (error.message?.includes('Invalid Refresh Token') ||
          error.message?.includes('refresh_token_not_found')) {
        console.log('Session expired or invalid, returning null')
        return null
      }
      throw error
    }

    return session
  } catch (error) {
    console.error('getSession failed:', error)
    throw error
  }
}

export const signInWithPassword = async (email: string, password: string) => {
  const supabase = createClient()
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password
  })
  if (error) throw error
  return data
}

export const signUpWithPassword = async (email: string, password: string, fullName: string) => {
  const supabase = createClient()
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      data: {
        full_name: fullName,
        display_name: fullName
      }
    }
  })
  if (error) throw error
  return data
}

export const resetPassword = async (email: string) => {
  const supabase = createClient()
  const { data, error } = await supabase.auth.resetPasswordForEmail(email, {
    redirectTo: `${window.location.origin}/reset-password`
  })
  if (error) throw error
  return data
}

export const connectGmailForExistingUser = async () => {
  const supabase = createClient()

  // Link Gmail OAuth to existing account
  const { data, error } = await supabase.auth.linkIdentity({
    provider: 'google',
    options: {
      redirectTo: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/email-agent/oauth/callback?next=/dashboard/settings`,
      queryParams: {
        access_type: 'offline',
        prompt: 'consent', // Force consent to ensure we get refresh token
        scope: 'email profile https://www.googleapis.com/auth/gmail.readonly'
      }
    }
  })

  if (error) throw error
  return data
}

export const unlinkGmail = async () => {
  const supabase = createClient()

  // Get current user identities
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) throw new Error('No user found')

  // Find Google identity
  const googleIdentity = user.identities?.find(identity => identity.provider === 'google')
  if (!googleIdentity) throw new Error('No Google identity found')

  // Unlink Google identity
  const { error } = await supabase.auth.unlinkIdentity(googleIdentity)
  if (error) throw error
}

export const checkGmailConnection = async () => {
  const supabase = createClient()

  // Get current user and check for Google identity
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return false

  // Check if user has Google identity with Gmail scope
  const googleIdentity = user.identities?.find(identity => identity.provider === 'google')
  return !!googleIdentity
}
