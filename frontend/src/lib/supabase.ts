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
      detectSessionInUrl: true
    },
    cookies: {
      get(name: string) {
        if (typeof window === 'undefined') return undefined
        const cookies = document.cookie.split(';')
        const cookie = cookies.find(c => c.trim().startsWith(`${name}=`))
        return cookie ? cookie.split('=')[1] : undefined
      },
      set(name: string, value: string, options: Record<string, string | number | boolean>) {
        if (typeof window === 'undefined') return
        const optionsString = Object.entries(options || {})
          .map(([key, val]) => {
            if (key === 'maxAge') return `max-age=${val}`
            if (key === 'sameSite') return `samesite=${val}`
            return `${key}=${val}`
          })
          .join('; ')
        document.cookie = `${name}=${value}; ${optionsString}`
      },
      remove(name: string, options: Record<string, string | number | boolean> = {}) {
        if (typeof window === 'undefined') return
        document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; ${Object.entries(options)
          .map(([key, val]) => `${key}=${val}`)
          .join('; ')}`
      }
    }
  })
}

// Auth utilities for client-side use
export const signInWithGoogle = async () => {
  const supabase = createClient()


  // Use signInWithOAuth with proper options for existing user detection
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: `${window.location.origin}/api/auth/callback`,
      queryParams: {
        access_type: 'offline',
        prompt: 'select_account', // This allows user to choose account but doesn't force re-consent
        scope: 'email profile https://www.googleapis.com/auth/gmail.readonly'
      }
    }
  })


  if (error) throw error
  return data
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
