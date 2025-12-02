"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { connectGmailForExistingUser, unlinkGmail, checkGmailConnection } from "@/lib/supabase"
import { useAuth } from "@/contexts/auth-context"
import {
  Mail,
  CheckCircle,
  AlertCircle,
  Loader2,
  RefreshCw,
  Unlink,
  Eye,
  Shield,
  Zap
} from "lucide-react"
import { cn } from "@/lib/utils"

interface GmailConnectionProps {
  onConnectionChange?: (connected: boolean) => void
  showAsCard?: boolean
  className?: string
}

export function GmailConnection({
  onConnectionChange,
  showAsCard = true,
  className
}: GmailConnectionProps) {
  const [isConnected, setIsConnected] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isConnecting, setIsConnecting] = useState(false)
  const [isDisconnecting, setIsDisconnecting] = useState(false)
  const [error, setError] = useState("")

  const { user } = useAuth()

  // Check Gmail connection status
  const checkConnection = async () => {
    if (!user) return

    try {
      setIsLoading(true)
      const connected = await checkGmailConnection()
      setIsConnected(connected)
      onConnectionChange?.(connected)
    } catch (error: unknown) {
      console.error('Error checking Gmail connection:', error)
      const errorObj = error as { message?: string }
      setError(errorObj.message || "Failed to check Gmail connection")
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    checkConnection()
  }, [user])

  // Connect Gmail
  const handleConnect = async () => {
    try {
      setIsConnecting(true)
      setError("")
      await connectGmailForExistingUser()
      // The OAuth flow will redirect, so we don't need to update state here
    } catch (error: unknown) {
      console.error('Error connecting Gmail:', error)
      const errorObj = error as { message?: string }
      setError(errorObj.message || "Failed to connect Gmail")
      setIsConnecting(false)
    }
  }

  // Disconnect Gmail
  const handleDisconnect = async () => {
    try {
      setIsDisconnecting(true)
      setError("")
      await unlinkGmail()
      setIsConnected(false)
      onConnectionChange?.(false)
    } catch (error: unknown) {
      console.error('Error disconnecting Gmail:', error)
      const errorObj = error as { message?: string }
      setError(errorObj.message || "Failed to disconnect Gmail")
    } finally {
      setIsDisconnecting(false)
    }
  }

  const features = [
    {
      icon: Eye,
      title: "Email Monitoring",
      description: "Automatically detect job-related emails and application updates"
    },
    {
      icon: Shield,
      title: "Secure Access",
      description: "Read-only access to your Gmail with industry-standard security"
    },
    {
      icon: Zap,
      title: "Real-time Updates",
      description: "Get instant notifications about application status changes"
    }
  ]

  const content = (
    <>
      {/* Connection Status */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className={cn(
            "w-3 h-3 rounded-full",
            isConnected ? "bg-green-400" : "bg-red-400"
          )} />
          <div>
            <h3 className="text-lg font-semibold text-cream-50">
              Gmail Integration
            </h3>
            <p className="text-sm text-cream-300">
              {isLoading ? "Checking connection..." :
               isConnected ? "Connected and monitoring emails" :
               "Not connected - Connect to enable email features"}
            </p>
          </div>
        </div>
        {isConnected && (
          <Badge className="bg-green-500/20 text-green-400 border-green-500/30">
            Active
          </Badge>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center p-3 mb-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400"
        >
          <AlertCircle className="w-4 h-4 mr-2 flex-shrink-0" />
          <span className="text-sm">{error}</span>
        </motion.div>
      )}

      {!isConnected && (
        <>
          {/* Why Connect Section */}
          <div className="mb-6">
            <h4 className="text-md font-medium text-cream-50 mb-3">
              Why connect your Gmail?
            </h4>
            <div className="space-y-3">
              {features.map((feature, index) => (
                <div key={index} className="flex items-start space-x-3">
                  <feature.icon className="w-5 h-5 text-accent-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <div className="text-sm font-medium text-cream-200">
                      {feature.title}
                    </div>
                    <div className="text-sm text-cream-300">
                      {feature.description}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Connect Button */}
          <Button
            onClick={handleConnect}
            disabled={isConnecting || isLoading}
            className="w-full bg-gradient-warm hover:bg-gradient-gold text-white glow-orange hover:glow-gold transition-all duration-300"
            size="lg"
          >
            {isConnecting ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Connecting...
              </>
            ) : (
              <>
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
                Connect Gmail
              </>
            )}
          </Button>

          {/* Privacy Note */}
          <div className="mt-4 p-3 bg-primary-700/50 rounded-lg border border-primary-600">
            <div className="flex items-start space-x-2">
              <Shield className="w-4 h-4 text-cream-400 mt-0.5 flex-shrink-0" />
              <div className="text-xs text-cream-300">
                <strong>Privacy & Security:</strong> We only request read-only access to detect
                job-related emails. Your email content is processed securely and never stored permanently.
              </div>
            </div>
          </div>
        </>
      )}

      {isConnected && (
        <>
          {/* Connected State */}
          <div className="mb-6">
            <div className="flex items-center p-4 bg-green-500/10 border border-green-500/20 rounded-lg">
              <CheckCircle className="w-5 h-5 text-green-400 mr-3" />
              <div>
                <div className="text-sm font-medium text-green-400">
                  Gmail Successfully Connected
                </div>
                <div className="text-sm text-cream-300">
                  Email monitoring is active. Job-related emails will be automatically detected.
                </div>
              </div>
            </div>
          </div>

          {/* Connection Management */}
          <div className="space-y-3">
            <Button
              onClick={checkConnection}
              disabled={isLoading}
              variant="outline"
              className="w-full border-primary-600 text-cream-200 hover:text-cream-50 hover:border-accent-500/50"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <RefreshCw className="w-4 h-4 mr-2" />
              )}
              Refresh Status
            </Button>

            <Button
              onClick={handleDisconnect}
              disabled={isDisconnecting}
              variant="destructive"
              className="w-full"
            >
              {isDisconnecting ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Unlink className="w-4 h-4 mr-2" />
              )}
              Disconnect Gmail
            </Button>
          </div>
        </>
      )}
    </>
  )

  if (!showAsCard) {
    return <div className={className}>{content}</div>
  }

  return (
    <Card className={cn("premium-card", className)}>
      <CardHeader>
        <CardTitle className="flex items-center text-cream-50">
          <Mail className="w-5 h-5 mr-2" />
          Gmail Integration
        </CardTitle>
        <CardDescription className="text-cream-300">
          Connect your Gmail to enable automatic email monitoring and job application tracking
        </CardDescription>
      </CardHeader>
      <CardContent>
        {content}
      </CardContent>
    </Card>
  )
}

// Compact version for dashboard/settings
export function GmailConnectionStatus({
  onConnectionChange,
  className
}: Pick<GmailConnectionProps, 'onConnectionChange' | 'className'>) {
  const [isConnected, setIsConnected] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  const { user } = useAuth()

  useEffect(() => {
    const checkConnection = async () => {
      if (!user) return

      try {
        const connected = await checkGmailConnection()
        setIsConnected(connected)
        onConnectionChange?.(connected)
      } catch (error) {
        console.error('Error checking Gmail connection:', error)
      } finally {
        setIsLoading(false)
      }
    }

    checkConnection()
  }, [user, onConnectionChange])

  if (isLoading) {
    return (
      <div className={cn("flex items-center space-x-2", className)}>
        <Loader2 className="w-4 h-4 animate-spin text-cream-400" />
        <span className="text-sm text-cream-300">Checking Gmail connection...</span>
      </div>
    )
  }

  return (
    <div className={cn("flex items-center space-x-2", className)}>
      <div className={cn(
        "w-2 h-2 rounded-full",
        isConnected ? "bg-green-400" : "bg-red-400"
      )} />
      <span className="text-sm text-cream-300">
        Gmail: {isConnected ? "Connected" : "Not Connected"}
      </span>
      {isConnected && (
        <Badge className="bg-green-500/20 text-green-400 border-green-500/30 text-xs">
          Active
        </Badge>
      )}
    </div>
  )
}