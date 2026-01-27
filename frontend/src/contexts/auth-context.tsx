"use client"

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { User, Session } from '@supabase/supabase-js'
import { createClient, signInWithGoogle, signOut, getCurrentUser, getSession, clearAllAuthData } from '@/lib/supabase'
import { useRouter } from 'next/navigation'

interface AuthContextType {
  user: User | null
  session: Session | null
  loading: boolean
  signIn: () => Promise<void>
  signOutUser: () => Promise<void>
  refreshUser: () => Promise<void>
  clearSession: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    let mounted = true
    let retryCount = 0
    const maxRetries = 3 // Reduced retries to prevent infinite loops
    const retryDelay = 500
    let lastErrorMessage = ''

    // Get initial session with comprehensive retry logic
    const getInitialSession = async (): Promise<void> => {
      if (!mounted) return

      try {
        // Progressive delay for retries with exponential backoff
        if (retryCount > 0) {
          const delay = retryDelay * Math.pow(1.5, retryCount - 1)
          await new Promise(resolve => setTimeout(resolve, delay))
        }

        const session = await getSession()

        if (!mounted) return

        if (session) {
          setSession(session)
          setUser(session.user)
          setLoading(false)
          return
        }

        // Check if we're on a protected route that requires authentication
        const isProtectedRoute = typeof window !== 'undefined' && window.location.pathname.startsWith('/dashboard')
        // Also check if we're coming from an OAuth callback (common case)
        const fromOAuthCallback = typeof window !== 'undefined' && window.location.search.includes('code=')
        const fromEmailConfirmation = typeof window !== 'undefined' && window.location.search.includes('token_hash=')

        if ((isProtectedRoute || fromOAuthCallback || fromEmailConfirmation) && retryCount < maxRetries) {
          retryCount++
          setTimeout(() => getInitialSession(), 0)
          return
        }

        // No session found after retries
        setSession(null)
        setUser(null)
        setLoading(false)
      } catch (error: any) {
        if (!mounted) return

        // Check for refresh token errors and stop retrying if we get the same error repeatedly
        const errorMessage = error?.message || ''
        const isRefreshTokenError = errorMessage.includes('Invalid Refresh Token') ||
          errorMessage.includes('refresh_token_not_found')

        if (isRefreshTokenError) {
          setSession(null)
          setUser(null)
          setLoading(false)
          return
        }

        // Only retry if it's not the same error and we haven't exceeded max retries
        if (retryCount < maxRetries && errorMessage !== lastErrorMessage) {
          lastErrorMessage = errorMessage
          retryCount++
          setTimeout(() => getInitialSession(), retryDelay * retryCount)
          return
        }

        // Clear any invalid session state after all retries
        setSession(null)
        setUser(null)
        setLoading(false)
      }
    }

    // Also set up auth state change listener
    const supabase = createClient()
    let authEventCount = 0
    const maxAuthEvents = 10 // Prevent infinite auth event loops

    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        authEventCount++

        // If we've had too many auth events in a short time, it might be a loop
        if (authEventCount > maxAuthEvents) {
          console.warn('🚨 AuthContext: Too many auth events, possible infinite loop detected. Clearing session.')
          await clearAllAuthData()
          setSession(null)
          setUser(null)
          setLoading(false)
          return
        }

        if (!mounted) return

        if (event === 'SIGNED_IN' && session) {
          setSession(session)
          setUser(session.user)
          setLoading(false)
        } else if (event === 'SIGNED_OUT') {
          setSession(null)
          setUser(null)
          setLoading(false)
        } else if (event === 'TOKEN_REFRESHED' && session) {
          setSession(session)
          setUser(session.user)
          setLoading(false)
        } else if (event === 'INITIAL_SESSION') {
          // Handle initial session event
          if (session) {
            setSession(session)
            setUser(session.user)
          } else {
            setSession(null)
            setUser(null)
          }
          setLoading(false)
        }

        // Reset auth event counter after a delay
        setTimeout(() => {
          authEventCount = Math.max(0, authEventCount - 1)
        }, 1000)
      }
    )

    getInitialSession()

    return () => {
      mounted = false
      subscription.unsubscribe()
    }
  }, [])

  const signIn = async () => {
    try {
      setLoading(true)
      await signInWithGoogle()
      // The redirect will happen automatically
    } catch (error) {
      console.error('Error signing in:', error)
      setLoading(false)
      throw error
    }
  }

  const signOutUser = async () => {
    try {
      setLoading(true)
      // Clear user state immediately to prevent showing protected content
      setUser(null)
      setSession(null)
      // Clear any stored session data
      await clearSession()
      // Sign out from Supabase
      await signOut()
      // Redirect to landing page
      router.push('/')
    } catch (error) {
      console.error('Error signing out:', error)
      // Even if signOut fails, we should still redirect
      router.push('/')
      throw error
    } finally {
      setLoading(false)
    }
  }

  const refreshUser = async () => {
    try {
      setLoading(true)
      const user = await getCurrentUser()
      setUser(user)
    } catch (error) {
      console.error('Error refreshing user:', error)
      setUser(null)
      setSession(null)
    } finally {
      setLoading(false)
    }
  }

  const clearSession = async () => {
    await clearAllAuthData()
  }

  const value = {
    user,
    session,
    loading,
    signIn,
    signOutUser,
    refreshUser,
    clearSession,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
