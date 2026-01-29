"use client"

import { Button } from "@/components/ui/button"
import { ArrowRight } from "lucide-react"
import { useAuth } from "@/contexts/auth-context"
import { useRouter, useSearchParams } from "next/navigation"
import { useState, useEffect, Suspense } from "react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { XCircle } from "lucide-react"

interface LandingPageCTAProps {
  size?: "default" | "lg"
  variant?: "default" | "outline"
  className?: string
}

function LandingPageCTAContent({
  size = "default",
  variant = "default",
  className = ""
}: LandingPageCTAProps) {
  const { user, signIn, loading } = useAuth()
  const router = useRouter()
  const searchParams = useSearchParams()
  const [isSigningIn, setIsSigningIn] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const errorParam = searchParams.get('error')
    if (errorParam) {
      setError(decodeURIComponent(errorParam))
      router.replace('/', { scroll: false })
    }
  }, [searchParams, router])

  const handleAction = async () => {
    if (user) {
      router.push('/dashboard')
    } else {
      try {
        setIsSigningIn(true)
        setError(null)
        await signIn()
      } catch (error) {
        console.error('Sign in error:', error)
        setError('Failed to start authentication. Please try again.')
      } finally {
        setIsSigningIn(false)
      }
    }
  }

  const getButtonText = () => {
    if (user) return "Go to Dashboard"
    if (isSigningIn) return "Signing In..."
    return "Try Prism Pro"
  }

  return (
    <div className="space-y-4">
      {error && (
        <Alert variant="destructive">
          <XCircle className="h-4 w-4" />
          <AlertDescription>
            {error}
          </AlertDescription>
        </Alert>
      )}

      <div className="text-center">
        <Button
          onClick={handleAction}
          disabled={loading || isSigningIn}
          size={size}
          variant={variant}
          className={className}
        >
          {getButtonText()}
          {!isSigningIn && <ArrowRight className="ml-2 w-5 h-5" />}
        </Button>
      </div>
    </div>
  )
}

export function LandingPageCTA(props: LandingPageCTAProps) {
  return (
    <Suspense fallback={
      <div className="text-center">
        <Button disabled size={props.size} variant={props.variant} className={props.className}>
          Loading...
        </Button>
      </div>
    }>
      <LandingPageCTAContent {...props} />
    </Suspense>
  )
}
