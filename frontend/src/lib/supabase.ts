import { createBrowserClient } from '@supabase/ssr'
import { getBrowserAppOrigin } from './url'

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
      debug: process.env.NODE_ENV === 'development',
      storage: {
        getItem: (key: string) => {
          if (typeof window === 'undefined') return null
          try {
            return localStorage.getItem(key)
          } catch (error) {
            console.warn(`Failed to get storage item ${key}:`, error)
            return null
          }
        },
        setItem: (key: string, value: string) => {
          if (typeof window === 'undefined') return
          try {
            localStorage.setItem(key, value)
          } catch (error) {
            console.warn(`Failed to set storage item ${key}:`, error)
          }
        },
        removeItem: (key: string) => {
          if (typeof window === 'undefined') return
          try {
            localStorage.removeItem(key)
          } catch (error) {
            console.warn(`Failed to remove storage item ${key}:`, error)
          }
        }
      }
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
      remove(name: string, options?: Record<string, unknown>) {
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

// Get the correct redirect URL based on environment
const getRedirectUrl = () => {
  return `${getBrowserAppOrigin()}/api/auth/callback`
}

// Auth utilities for client-side use
export const signInWithGoogle = async () => {
  const supabase = createClient()

  try {
    // Clear any existing corrupted session first
    await clearAllAuthData()

    const redirectUrl = getRedirectUrl()
    console.log('🔗 OAuth redirect URL:', redirectUrl)

    // Use signInWithOAuth with proper PKCE handling
    const { data, error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: redirectUrl,
        skipBrowserRedirect: false,
        queryParams: {
          access_type: 'offline',
          prompt: 'consent', // Force consent to ensure fresh tokens
          scope: 'openid email profile'
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
        console.log('Session expired or invalid, clearing all auth data')
        // Clear corrupted session data immediately
        await clearAllAuthData()
        return null
      }
      throw error
    }

    return session
  } catch (error) {
    console.error('getSession failed:', error)
    // If any other error occurs, also clear auth data to prevent loops
    if (error.message?.includes('Invalid Refresh Token') ||
      error.message?.includes('refresh_token_not_found')) {
      console.log('Clearing auth data due to session error')
      await clearAllAuthData()
    }
    throw error
  }
}

// Utility function to clear all authentication data
export const clearAllAuthData = async () => {
  try {
    const supabase = createClient()

    // Force sign out from Supabase
    await supabase.auth.signOut({ scope: 'local' })

    // Clear browser storage
    if (typeof window !== 'undefined') {
      // Clear localStorage
      const localKeys = Object.keys(localStorage)
      localKeys.forEach(key => {
        if (key.startsWith('sb-') || key.includes('supabase') || key.includes('auth')) {
          localStorage.removeItem(key)
        }
      })

      // Clear sessionStorage
      const sessionKeys = Object.keys(sessionStorage)
      sessionKeys.forEach(key => {
        if (key.startsWith('sb-') || key.includes('supabase') || key.includes('auth')) {
          sessionStorage.removeItem(key)
        }
      })

      // Clear cookies
      const cookies = document.cookie.split(';')
      cookies.forEach(cookie => {
        const [name] = cookie.split('=')
        const cookieName = name?.trim()
        if (cookieName && (cookieName.startsWith('sb-') || cookieName.includes('supabase'))) {
          document.cookie = `${cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/`
        }
      })

      console.log('✅ All authentication data cleared successfully')
    }
  } catch (error) {
    console.warn('Error clearing auth data:', error)
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
