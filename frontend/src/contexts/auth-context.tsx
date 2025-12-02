"use client"

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { User, Session } from '@supabase/supabase-js'
import { createClient, signInWithGoogle, signOut, getCurrentUser, getSession } from '@/lib/supabase'
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
    const maxRetries = 5 // Increased retries for auth-critical flows
    const retryDelay = 300

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
        console.log(`AuthContext: Session attempt ${retryCount + 1}:`, {
          hasSession: !!session,
          hasUser: !!session?.user,
          userId: session?.user?.id,
          pathname: typeof window !== 'undefined' ? window.location.pathname : 'SSR',
          retryCount,
          timestamp: new Date().toISOString()
        })

        if (!mounted) return

        if (session) {
          setSession(session)
          setUser(session.user)
          setLoading(false)
          console.log(`✅ AuthContext: Session loaded successfully after ${retryCount + 1} attempts`)
          return
        }

        // Check if we're on a protected route that requires authentication
        const isProtectedRoute = typeof window !== 'undefined' && window.location.pathname.startsWith('/dashboard')
        // Also check if we're coming from an OAuth callback (common case)
        const fromOAuthCallback = typeof window !== 'undefined' && window.location.search.includes('code=')
        const fromEmailConfirmation = typeof window !== 'undefined' && window.location.search.includes('token_hash=')

        if ((isProtectedRoute || fromOAuthCallback || fromEmailConfirmation) && retryCount < maxRetries) {
          retryCount++
          console.log(`🔄 AuthContext: Retrying session retrieval (${retryCount}/${maxRetries}) - Protected route or callback detected`)
          setTimeout(() => getInitialSession(), 0)
          return
        }

        // No session found after retries
        console.log(`❌ AuthContext: No session found after ${retryCount + 1} attempts`)
        setSession(null)
        setUser(null)
        setLoading(false)
      } catch (error) {
        console.error('❌ AuthContext: Error getting initial session:', error)
        if (!mounted) return

        if (retryCount < maxRetries) {
          retryCount++
          console.log(`🔄 AuthContext: Error recovery retry (${retryCount}/${maxRetries})...`)
          setTimeout(() => getInitialSession(), retryDelay * retryCount)
          return
        }

        // Clear any invalid session state after all retries
        console.log(`❌ AuthContext: Giving up after ${retryCount + 1} attempts`)
        setSession(null)
        setUser(null)
        setLoading(false)
      }
    }

    // Also set up auth state change listener
    const supabase = createClient()
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        console.log('✉️ AuthContext: Auth state change:', {
          event,
          hasSession: !!session,
          hasUser: !!session?.user,
          userId: session?.user?.id,
          pathname: typeof window !== 'undefined' ? window.location.pathname : 'SSR',
          timestamp: new Date().toISOString()
        })

        if (!mounted) return

        if (event === 'SIGNED_IN' && session) {
          console.log('✅ AuthContext: User signed in via auth state change')
          setSession(session)
          setUser(session.user)
          setLoading(false)
        } else if (event === 'SIGNED_OUT') {
          console.log('🚪 AuthContext: User signed out via auth state change')
          setSession(null)
          setUser(null)
          setLoading(false)
        } else if (event === 'TOKEN_REFRESHED' && session) {
          console.log('🔄 AuthContext: Token refreshed via auth state change')
          setSession(session)
          setUser(session.user)
          setLoading(false)
        } else if (event === 'INITIAL_SESSION') {
          console.log('🎯 AuthContext: Initial session event received')
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
      clearSession()
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

  const clearSession = () => {
    // Clear any stored session data
    if (typeof window !== 'undefined') {
      try {
        // Clear legacy token storage
        localStorage.removeItem('supabase.auth.token')
        sessionStorage.removeItem('supabase.auth.token')

        // Clear all Supabase-related items from localStorage
        const keys = Object.keys(localStorage)
        keys.forEach(key => {
          if (key.startsWith('sb-') || key.includes('supabase')) {
            localStorage.removeItem(key)
          }
        })

        // Clear sessionStorage too
        const sessionKeys = Object.keys(sessionStorage)
        sessionKeys.forEach(key => {
          if (key.startsWith('sb-') || key.includes('supabase')) {
            sessionStorage.removeItem(key)
          }
        })

        console.log('AuthContext: Session storage cleared')
      } catch (error) {
        console.warn('AuthContext: Failed to clear session storage:', error)
      }
    }
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
