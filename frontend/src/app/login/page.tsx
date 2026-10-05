"use client"

import { useState, useEffect, Suspense } from "react"
import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"
import { Logo } from "@/components/logo"
import { useAuth } from "@/contexts/auth-context"
import { useRouter, useSearchParams } from "next/navigation"
import { createClient, checkGmailConnection } from "@/lib/supabase"
import { useTheme } from "@/contexts/theme-context"
import Link from "next/link"
import {
  Eye,
  EyeOff,
  Mail,
  Lock,
  ArrowRight,
  AlertCircle,
  CheckCircle,
  ArrowLeft,
  Loader2,
  Sun,
  Moon
} from "lucide-react"
import { cn } from "@/lib/utils"
// Gmail connection component temporarily disabled after refactoring

// Animation variants
const _fadeInVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6 } }
}

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
}

const staggerItem = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 }
}

// Form validation
const validateEmail = (email: string) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

const validatePassword = (password: string) => {
  return password.length >= 6
}

function LoginForm() {
  const [isSignUp, setIsSignUp] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    confirmPassword: "",
    fullName: ""
  })
  const [formErrors, setFormErrors] = useState<Record<string, string>>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [authError, setAuthError] = useState("")
  const [authSuccess, setAuthSuccess] = useState("")
  const [showGmailConnection, setShowGmailConnection] = useState(false)
  const [_gmailConnected, _setGmailConnected] = useState(false)

  const { user, signIn, loading } = useAuth()
  const router = useRouter()
  const searchParams = useSearchParams()
  const redirectTo = searchParams.get('redirectTo') || '/dashboard'
  const { isDark, toggleTheme } = useTheme()

  // Handle URL error parameters
  useEffect(() => {
    const error = searchParams.get('error')
    const details = searchParams.get('details')

    if (error) {
      let errorMessage = ""

      switch (error) {
        case 'auth_failed':
          errorMessage = "Authentication failed. Please try again."
          break
        case 'access_denied':
          errorMessage = "Access was denied. Please try again and make sure to grant permissions."
          break
        case 'session_failed':
          errorMessage = details ? `Session creation failed: ${decodeURIComponent(details)}` : "Failed to create session. Please try again."
          break
        case 'callback_error':
          errorMessage = "An error occurred during authentication. Please try again."
          break
        case 'no_code':
          errorMessage = "No authorization code received. Please try again."
          break
        default:
          errorMessage = `Authentication error: ${error}. Please try again.`
      }

      setAuthError(errorMessage)
    }
  }, [searchParams])

  // Redirect if already authenticated
  useEffect(() => {
    if (user && !loading) {
      router.push(redirectTo)
    }
  }, [user, loading, router, redirectTo])

  // Handle form input changes
  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    // Clear field-specific error when user starts typing
    if (formErrors[field]) {
      setFormErrors(prev => ({ ...prev, [field]: "" }))
    }
    setAuthError("")
  }

  // Validate form
  const validateForm = () => {
    const errors: Record<string, string> = {}

    if (!formData.email) {
      errors.email = "Email is required"
    } else if (!validateEmail(formData.email)) {
      errors.email = "Please enter a valid email address"
    }

    if (!formData.password) {
      errors.password = "Password is required"
    } else if (!validatePassword(formData.password)) {
      errors.password = "Password must be at least 6 characters long"
    }

    if (isSignUp) {
      if (!formData.fullName.trim()) {
        errors.fullName = "Full name is required"
      }

      if (!formData.confirmPassword) {
        errors.confirmPassword = "Please confirm your password"
      } else if (formData.password !== formData.confirmPassword) {
        errors.confirmPassword = "Passwords do not match"
      }
    }

    setFormErrors(errors)
    return Object.keys(errors).length === 0
  }

  // Handle Google OAuth sign in
  const handleGoogleSignIn = async () => {
    try {
      setIsSubmitting(true)
      setAuthError("")
      await signIn()
    } catch (error: unknown) {
      console.error('Google sign in error:', error)
      const errorMessage = error instanceof Error ? error.message : "Failed to sign in with Google. Please try again."
      setAuthError(errorMessage)
    } finally {
      setIsSubmitting(false)
    }
  }

  // Handle email/password authentication
  const handleEmailAuth = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateForm()) {
      return
    }

    setIsSubmitting(true)
    setAuthError("")
    setAuthSuccess("")

    try {
      const supabase = createClient()

      if (isSignUp) {
        // Sign up new user
        const { data, error } = await supabase.auth.signUp({
          email: formData.email,
          password: formData.password,
          options: {
            data: {
              full_name: formData.fullName,
              display_name: formData.fullName
            }
          }
        })

        if (error) throw error

        if (data.user && !data.session) {
          // Email confirmation required
          setAuthSuccess("Please check your email and click the confirmation link to complete your registration.")
        } else if (data.session) {
          // Auto sign in successful - check Gmail connection
          const gmailConnected = await checkGmailConnection()
          if (!gmailConnected) {
            setAuthSuccess("Account created successfully! Let's connect your Gmail for email monitoring.")
            setShowGmailConnection(true)
          } else {
            setAuthSuccess("Account created successfully! Redirecting to dashboard...")
            setTimeout(() => router.push(redirectTo), 2000)
          }
        }
      } else {
        // Sign in existing user
        const { data, error } = await supabase.auth.signInWithPassword({
          email: formData.email,
          password: formData.password
        })

        if (error) throw error

        if (data.session) {
          setAuthSuccess("Sign in successful! Redirecting to dashboard...")
          setTimeout(() => router.push(redirectTo), 1500)
        }
      }
    } catch (error: unknown) {
      console.error('Auth error:', error)

      // Handle specific error cases
      const errorObj = error as { message?: string }
      if (errorObj.message?.includes("Invalid login credentials")) {
        setAuthError("Invalid email or password. Please check your credentials and try again.")
      } else if (errorObj.message?.includes("Email not confirmed")) {
        setAuthError("Please check your email and click the confirmation link before signing in.")
      } else if (errorObj.message?.includes("User already registered")) {
        setAuthError("An account with this email already exists. Please sign in instead.")
      } else {
        setAuthError(errorObj.message || `Failed to ${isSignUp ? 'create account' : 'sign in'}. Please try again.`)
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  // Don't show login page if user is already authenticated
  if (user) {
    return null
  }

  return (
    <div className="min-h-screen bg-background relative overflow-hidden flex items-center justify-center">
      {/* Background Effects - subtle and unified */}
      <div className="absolute inset-0">
        <div className="grain-overlay"></div>
        <motion.div
          className={`absolute top-20 left-20 w-96 h-96 rounded-full blur-3xl ${isDark
              ? 'bg-gradient-radial from-white/5 to-transparent'
              : 'bg-gradient-radial from-black/5 to-transparent'
            }`}
          animate={{
            x: [0, 50, 0],
            y: [0, -30, 0],
          }}
          transition={{ duration: 30, repeat: Infinity, ease: "linear" }}
        />
        <motion.div
          className={`absolute bottom-20 right-20 w-96 h-96 rounded-full blur-3xl ${isDark
              ? 'bg-gradient-radial from-white/3 to-transparent'
              : 'bg-gradient-radial from-black/3 to-transparent'
            }`}
          animate={{
            x: [0, -50, 0],
            y: [0, 30, 0],
          }}
          transition={{ duration: 25, repeat: Infinity, ease: "linear" }}
        />
      </div>

      <div className="relative z-10 w-full max-w-md mx-auto px-6">
        {/* Back to Home Link */}
        <motion.div
          className="mb-8"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
        >
          <Link
            href="/"
            className="inline-flex items-center text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Home
          </Link>
        </motion.div>

        {/* Theme Toggle */}
        <motion.div
          className="flex justify-end mb-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5 }}
        >
          <button
            onClick={toggleTheme}
            className="p-2 rounded-full border border-border hover:bg-muted/50 transition-colors"
            aria-label="Toggle Theme"
          >
            {isDark ? (
              <Sun className="h-5 w-5 text-foreground" />
            ) : (
              <Moon className="h-5 w-5 text-foreground" />
            )}
          </button>
        </motion.div>

        {/* Logo and Branding */}
        <motion.div
          className="text-center mb-8"
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
        >
          <motion.div variants={staggerItem} className="flex justify-center mb-4">
            <Logo size={48} showText={false} />
          </motion.div>
          <motion.h1
            variants={staggerItem}
            className="text-3xl font-bold tracking-tight text-foreground mb-2"
          >
            PRISM <span className="opacity-50 font-light">PRO</span>
          </motion.h1>
          <motion.p
            variants={staggerItem}
            className="text-muted-foreground"
          >
            {isSignUp ? "Recruiter-grade resume prep starts here" : "Sign in to your workspace"}
          </motion.p>
        </motion.div>

        {/* Main Login Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          <Card className="premium-card border border-border">
            <CardHeader className="space-y-4">
              <CardTitle className="text-2xl text-center text-foreground">
                {isSignUp ? "Create Account" : "Sign In"}
              </CardTitle>
              <CardDescription className="text-center text-muted-foreground">
                {isSignUp
                  ? "Join engineers and PMs who prep smarter, not longer"
                  : "Welcome back — your resume work continues here"
                }
              </CardDescription>
            </CardHeader>

            <CardContent className="space-y-6">
              {/* Auth Error/Success Messages */}
              {authError && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex items-center p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400"
                >
                  <AlertCircle className="w-4 h-4 mr-2 shrink-0" />
                  <span className="text-sm">{authError}</span>
                </motion.div>
              )}

              {authSuccess && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex items-center p-3 bg-green-500/10 border border-green-500/20 rounded-lg text-green-400"
                >
                  <CheckCircle className="w-4 h-4 mr-2 shrink-0" />
                  <span className="text-sm">{authSuccess}</span>
                </motion.div>
              )}

              {/* Google OAuth Button */}
              <Button
                onClick={handleGoogleSignIn}
                disabled={isSubmitting || loading}
                className="w-full bg-background border border-border hover:bg-muted/50 text-foreground transition-all duration-300"
                size="lg"
              >
                {isSubmitting ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <svg className="w-4 h-4 mr-2" viewBox="0 0 24 24">
                    <path
                      fill="currentColor"
                      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                    />
                    <path
                      fill="currentColor"
                      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                    />
                    <path
                      fill="currentColor"
                      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                    />
                    <path
                      fill="currentColor"
                      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                    />
                  </svg>
                )}
                Continue with Google
              </Button>

              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <Separator className="w-full" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-card px-2 text-muted-foreground">Or continue with email</span>
                </div>
              </div>

              {/* Email/Password Form */}
              <form onSubmit={handleEmailAuth} className="space-y-4">
                {isSignUp && (
                  <div className="space-y-2">
                    <Label htmlFor="fullName" className="text-foreground">Full Name</Label>
                    <Input
                      id="fullName"
                      type="text"
                      placeholder="Enter your full name"
                      value={formData.fullName}
                      onChange={(e) => handleInputChange("fullName", e.target.value)}
                      className={cn(
                        "bg-background border-border text-foreground placeholder:text-muted-foreground",
                        "focus:border-ring focus:ring-ring/20",
                        formErrors.fullName && "border-destructive focus:border-destructive"
                      )}
                      disabled={isSubmitting}
                    />
                    {formErrors.fullName && (
                      <p className="text-sm text-destructive">{formErrors.fullName}</p>
                    )}
                  </div>
                )}

                <div className="space-y-2">
                  <Label htmlFor="email" className="text-foreground">Email</Label>
                  <div className="relative">
                    <Input
                      id="email"
                      type="email"
                      placeholder="Enter your email"
                      value={formData.email}
                      onChange={(e) => handleInputChange("email", e.target.value)}
                      className={cn(
                        "bg-background border-border text-foreground placeholder:text-muted-foreground pl-10",
                        "focus:border-ring focus:ring-ring/20",
                        formErrors.email && "border-destructive focus:border-destructive"
                      )}
                      disabled={isSubmitting}
                    />
                    <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  </div>
                  {formErrors.email && (
                    <p className="text-sm text-destructive">{formErrors.email}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password" className="text-foreground">Password</Label>
                  <div className="relative">
                    <Input
                      id="password"
                      type={showPassword ? "text" : "password"}
                      placeholder={isSignUp ? "Create a password (min. 6 characters)" : "Enter your password"}
                      value={formData.password}
                      onChange={(e) => handleInputChange("password", e.target.value)}
                      className={cn(
                        "bg-background border-border text-foreground placeholder:text-muted-foreground pl-10 pr-10",
                        "focus:border-ring focus:ring-ring/20",
                        formErrors.password && "border-destructive focus:border-destructive"
                      )}
                      disabled={isSubmitting}
                    />
                    <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground hover:text-foreground"
                      disabled={isSubmitting}
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  {formErrors.password && (
                    <p className="text-sm text-destructive">{formErrors.password}</p>
                  )}
                </div>

                {isSignUp && (
                  <div className="space-y-2">
                    <Label htmlFor="confirmPassword" className="text-foreground">Confirm Password</Label>
                    <div className="relative">
                      <Input
                        id="confirmPassword"
                        type={showPassword ? "text" : "password"}
                        placeholder="Confirm your password"
                        value={formData.confirmPassword}
                        onChange={(e) => handleInputChange("confirmPassword", e.target.value)}
                        className={cn(
                          "bg-background border-border text-foreground placeholder:text-muted-foreground pl-10",
                          "focus:border-ring focus:ring-ring/20",
                          formErrors.confirmPassword && "border-destructive focus:border-destructive"
                        )}
                        disabled={isSubmitting}
                      />
                      <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    </div>
                    {formErrors.confirmPassword && (
                      <p className="text-sm text-destructive">{formErrors.confirmPassword}</p>
                    )}
                  </div>
                )}

                <Button
                  type="submit"
                  disabled={isSubmitting || loading}
                  className="w-full bg-primary text-primary-foreground hover:bg-primary/90 transition-all duration-300"
                  size="lg"
                >
                  {isSubmitting ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <>
                      {isSignUp ? "Create Account" : "Sign In"}
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </>
                  )}
                </Button>
              </form>

              {/* Toggle between Sign In / Sign Up */}
              <div className="text-center pt-4 border-t border-border">
                <p className="text-muted-foreground">
                  {isSignUp ? "Already have an account?" : "New to Prism Pro?"}
                  {" "}
                  <button
                    onClick={() => {
                      setIsSignUp(!isSignUp)
                      setFormData({ email: "", password: "", confirmPassword: "", fullName: "" })
                      setFormErrors({})
                      setAuthError("")
                      setAuthSuccess("")
                    }}
                    className="text-primary hover:text-primary/80 font-medium transition-colors"
                    disabled={isSubmitting}
                  >
                    {isSignUp ? "Sign in here" : "Create account"}
                  </button>
                </p>
              </div>

              {!isSignUp && (
                <div className="text-center">
                  <Link
                    href="/forgot-password"
                    className="text-sm text-muted-foreground hover:text-primary transition-colors"
                  >
                    Forgot your password?
                  </Link>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* Gmail Connection Modal */}
        {showGmailConnection && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="mt-6"
          >
            <Card className="max-w-md mx-auto">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Mail className="w-5 h-5" />
                  Gmail Connection
                </CardTitle>
                <CardDescription>
                  Gmail connection temporarily disabled during refactoring.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button
                  onClick={() => router.push('/dashboard')}
                  className="w-full"
                >
                  Continue to Dashboard
                </Button>
              </CardContent>
            </Card>
            <Card className="max-w-md mx-auto">
              <CardContent className="p-4">
                <p className="text-sm text-muted-foreground">Gmail connection component is temporarily disabled.</p>
              </CardContent>
            </Card>

            {/* Skip for now option */}
            <div className="text-center mt-4">
              <button
                onClick={() => {
                  setAuthSuccess("Account created successfully! Redirecting to dashboard...")
                  setTimeout(() => router.push(redirectTo), 1500)
                }}
                className="text-sm text-muted-foreground hover:text-primary transition-colors underline"
              >
                Skip for now (you can connect Gmail later in settings)
              </button>
            </div>
          </motion.div>
        )}

        {/* Footer */}
        <motion.div
          className="text-center mt-8 text-sm text-muted-foreground"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.4 }}
        >
          <p>
            By continuing, you agree to our{" "}
            <Link href="/terms" className="text-primary hover:text-primary/80">
              Terms of Service
            </Link>{" "}
            and{" "}
            <Link href="/privacy" className="text-primary hover:text-primary/80">
              Privacy Policy
            </Link>
          </p>
        </motion.div>
      </div>
    </div>
  )
}

export default function LoginPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-foreground">Loading...</div>
      </div>
    }>
      <LoginForm />
    </Suspense>
  )
}