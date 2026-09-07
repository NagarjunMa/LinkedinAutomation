"use client"

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/auth-context'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Loader2, Shield } from 'lucide-react'

interface ProtectedRouteProps {
  children: React.ReactNode
  fallback?: React.ReactNode
}

export function ProtectedRoute({ children, fallback }: ProtectedRouteProps) {
  const [isTestBypass, setIsTestBypass] = useState(false)
  const { user, loading } = useAuth()
  const router = useRouter()
  const [showAuthRequired, setShowAuthRequired] = useState(false)

  useEffect(() => {
    // Reading document.cookie during render makes the server and first client
    // render disagree. Resolve this non-production E2E bypass after hydration
    // so production auth behavior and SSR markup remain deterministic.
    if (process.env.NODE_ENV !== 'production') {
      setIsTestBypass(document.cookie.includes('test-bypass-auth=1'))
    }
  }, [])

  useEffect(() => {
    if (isTestBypass) return
    if (!loading && !user) {
      console.log('ProtectedRoute: No user, redirecting to landing page')
      // Add a small delay to prevent showing auth required screen during logout
      const timer = setTimeout(() => {
        setShowAuthRequired(true)
        router.push('/')
      }, 100) // Small delay to allow logout redirect to complete

      return () => clearTimeout(timer)
    } else if (user) {
      setShowAuthRequired(false)
    }
  }, [user, loading, router, isTestBypass])

  if (isTestBypass) {
    return <>{children}</>
  }

  const handleGoToLanding = () => {
    console.log('ProtectedRoute: Go to Landing Page button clicked')
    console.log('ProtectedRoute: Attempting router.push("/")')
    router.push('/')
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <CardTitle>Loading...</CardTitle>
            <CardDescription>Please wait while we verify your authentication</CardDescription>
          </CardHeader>
          <CardContent className="flex justify-center">
            <Loader2 className="h-8 w-8 animate-spin" />
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!user && showAuthRequired) {
    if (fallback) {
      return <>{fallback}</>
    }

    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="mx-auto mb-4 w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center">
              <Shield className="h-8 w-8 text-primary" />
            </div>
            <CardTitle>Authentication Required</CardTitle>
            <CardDescription>
              You need to sign in to access this page
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button
              onClick={handleGoToLanding}
              className="w-full"
            >
              Go to Landing Page
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  // If no user but not showing auth required yet, show loading
  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <CardTitle>Loading...</CardTitle>
            <CardDescription>Please wait while we verify your authentication</CardDescription>
          </CardHeader>
          <CardContent className="flex justify-center">
            <Loader2 className="h-8 w-8 animate-spin" />
          </CardContent>
        </Card>
      </div>
    )
  }

  return <>{children}</>
}
