"use client"

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Loader2, Mail, CheckCircle, XCircle, ExternalLink } from 'lucide-react'
import { emailAgentApi } from '@/app/lib/api'

interface GmailConnectionProps {
    userId: string
}

interface ConnectionStatus {
    connected: boolean
    gmail_email?: string
    last_sync?: string
    total_emails_processed?: number
    recent_events?: Array<{
        id: number
        sender_email: string
        subject: string
        email_type: string
        confidence_score: number
        created_at: string
    }>
}

export function GmailConnection({ userId }: GmailConnectionProps) {
    const router = useRouter()
    const [status, setStatus] = useState<ConnectionStatus | null>(null)
    const [isConnecting, setIsConnecting] = useState(false)
    const [isProcessing, setIsProcessing] = useState(false)
    const [authUrl, setAuthUrl] = useState<string | null>(null)
    const [error, setError] = useState<string | null>(null)
    const [userEmail, setUserEmail] = useState<string>('')
    const [showSuccess, setShowSuccess] = useState(false)

    useEffect(() => {
        fetchStatus()
    }, [userId])

    // Check for OAuth callback success or error
    useEffect(() => {
        const urlParams = new URLSearchParams(window.location.search)
        const success = urlParams.get('success')
        const gmailEmail = urlParams.get('gmail_email')
        const error = urlParams.get('error')

        if (success === 'true' && gmailEmail) {
            setShowSuccess(true)
            setError(null)
            // Clear URL parameters
            window.history.replaceState({}, document.title, window.location.pathname)

            // Refresh status to show connected state
            fetchStatus()

            // Redirect to dashboard after 2 seconds
            setTimeout(() => {
                router.push('/dashboard')
            }, 2000)
        } else if (error) {
            setError(decodeURIComponent(error))
            // Clear URL parameters
            window.history.replaceState({}, document.title, window.location.pathname)
        }
    }, [router])

    const fetchStatus = async () => {
        try {
            const response = await emailAgentApi.getGmailStatus(userId)
            setStatus(response)
            setError(null)
        } catch (err: any) {
            console.error('Failed to fetch Gmail status:', err)
            setError(err.message || 'Failed to fetch status')
        }
    }

    const connectGmail = async () => {
        if (!userEmail.trim()) {
            setError('Please enter your email address')
            return
        }

        setIsConnecting(true)
        setError(null)

        try {
            console.log('Connecting Gmail...', userEmail)
            const response = await emailAgentApi.connectGmail(userId, userEmail)
            console.log('Response:', response)

            if (response.status === 'auth_required') {
                setAuthUrl(response.auth_url)
                // Open the authorization URL in a new popup window
                window.open(response.auth_url, '_blank', 'width=600,height=700')
            } else if (response.status === 'connected') {
                await fetchStatus()
                setShowSuccess(true)
                // Redirect to dashboard after successful connection
                setTimeout(() => {
                    router.push('/dashboard')
                }, 2000)
            }
        } catch (err: any) {
            console.error('Failed to connect Gmail:', err)
            setError(err.message || 'Failed to connect Gmail')
        } finally {
            setIsConnecting(false)
        }
    }

    const processEmails = async () => {
        setIsProcessing(true)
        setError(null)

        try {
            const response = await emailAgentApi.processEmails(userId)

            if (response.success) {
                await fetchStatus()
                // You could show a success message here
            }
        } catch (err: any) {
            console.error('Failed to process emails:', err)
            setError(err.message || 'Failed to process emails')
        } finally {
            setIsProcessing(false)
        }
    }

    const disconnectGmail = async () => {
        try {
            await emailAgentApi.disconnectGmail(userId)
            await fetchStatus()
            setError(null)
        } catch (err: any) {
            console.error('Failed to disconnect Gmail:', err)
            setError(err.message || 'Failed to disconnect Gmail')
        }
    }

    return (
        <Card className="w-full">
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <Mail className="h-5 w-5" />
                    Gmail Connection
                </CardTitle>
                <CardDescription>
                    Connect your Gmail account to automatically track job application emails using Google OAuth
                </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
                {error && (
                    <Alert variant="destructive">
                        <XCircle className="h-4 w-4" />
                        <AlertDescription>{error}</AlertDescription>
                    </Alert>
                )}

                {showSuccess && (
                    <Alert>
                        <CheckCircle className="h-4 w-4" />
                        <AlertDescription>
                            Gmail connected successfully! Redirecting to dashboard...
                        </AlertDescription>
                    </Alert>
                )}

                {authUrl && (
                    <Alert>
                        <ExternalLink className="h-4 w-4" />
                        <AlertDescription>
                            Please complete Google authorization in the popup window.
                            <br />
                            <a
                                href={authUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-blue-600 hover:underline"
                            >
                                Click here if the popup didn't open
                            </a>
                        </AlertDescription>
                    </Alert>
                )}

                {!status?.connected && (
                    <div className="space-y-2">
                        <Label htmlFor="email">Email Address</Label>
                        <Input
                            id="email"
                            type="email"
                            placeholder="Enter your Gmail address"
                            value={userEmail}
                            onChange={(e) => setUserEmail(e.target.value)}
                            onKeyPress={(e) => {
                                if (e.key === 'Enter' && !isConnecting) {
                                    connectGmail()
                                }
                            }}
                        />
                        <p className="text-xs text-muted-foreground">
                            This will be used to connect your Gmail account for email tracking
                        </p>
                    </div>
                )}

                {status && (
                    <div className="space-y-2">
                        <div className="flex items-center justify-between">
                            <span className="text-sm font-medium">Status:</span>
                            <Badge variant={status.connected ? "default" : "secondary"}>
                                {status.connected ? (
                                    <>
                                        <CheckCircle className="h-3 w-3 mr-1" />
                                        Connected
                                    </>
                                ) : (
                                    "Not Connected"
                                )}
                            </Badge>
                        </div>

                        {status.connected && status.gmail_email && (
                            <div className="flex items-center justify-between">
                                <span className="text-sm font-medium">Gmail Account:</span>
                                <span className="text-sm text-muted-foreground">{status.gmail_email}</span>
                            </div>
                        )}

                        {status.last_sync && (
                            <div className="flex items-center justify-between">
                                <span className="text-sm font-medium">Last Sync:</span>
                                <span className="text-sm text-muted-foreground">
                                    {new Date(status.last_sync).toLocaleString()}
                                </span>
                            </div>
                        )}

                        {status.total_emails_processed !== undefined && (
                            <div className="flex items-center justify-between">
                                <span className="text-sm font-medium">Emails Processed:</span>
                                <span className="text-sm text-muted-foreground">{status.total_emails_processed}</span>
                            </div>
                        )}
                    </div>
                )}

                <div className="flex gap-2">
                    {!status?.connected ? (
                        <Button
                            onClick={connectGmail}
                            disabled={isConnecting || !userEmail.trim()}
                            className="flex-1"
                        >
                            {isConnecting ? (
                                <>
                                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                    Connecting...
                                </>
                            ) : (
                                <>
                                    <Mail className="h-4 w-4 mr-2" />
                                    Connect Gmail
                                </>
                            )}
                        </Button>
                    ) : (
                        <>
                            <Button
                                onClick={processEmails}
                                disabled={isProcessing}
                                variant="outline"
                                className="flex-1"
                            >
                                {isProcessing ? (
                                    <>
                                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                        Processing...
                                    </>
                                ) : (
                                    'Process Emails'
                                )}
                            </Button>
                            <Button
                                onClick={disconnectGmail}
                                variant="destructive"
                            >
                                Disconnect
                            </Button>
                        </>
                    )}
                </div>
            </CardContent>
        </Card>
    )
} 