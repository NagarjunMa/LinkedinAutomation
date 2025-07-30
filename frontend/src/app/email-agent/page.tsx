"use client"

import { useState, useEffect } from 'react'
import { GmailConnection, EmailDashboard } from '@/components/email-agent'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { CheckCircle } from 'lucide-react'

export default function EmailAgentPage() {
    // For development, using a test user ID
    const testUserId = "999"
    const [showSuccess, setShowSuccess] = useState(false)

    // Check for OAuth callback success
    useEffect(() => {
        const urlParams = new URLSearchParams(window.location.search)
        const success = urlParams.get('success')
        const gmailEmail = urlParams.get('gmail_email')
        
        if (success === 'true' && gmailEmail) {
            setShowSuccess(true)
            // Clear URL parameters
            window.history.replaceState({}, document.title, window.location.pathname)
        }
    }, [])

    return (
        <div className="container mx-auto p-6 space-y-6">
            <div>
                <h1 className="text-3xl font-bold mb-2">Email Agent</h1>
                <p className="text-muted-foreground">
                    Automatically track and classify job application emails from your Gmail account using Google OAuth.
                </p>
            </div>

            {showSuccess && (
                <Alert>
                    <CheckCircle className="h-4 w-4" />
                    <AlertDescription>
                        Gmail connected successfully! You can now process emails and view analytics.
                    </AlertDescription>
                </Alert>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <GmailConnection userId={testUserId} />
                <div className="space-y-4">
                    <div className="p-4 border rounded-lg bg-muted/50">
                        <h3 className="font-semibold mb-2">Development Notes</h3>
                        <ul className="text-sm space-y-1 text-muted-foreground">
                            <li>• Test User ID: {testUserId}</li>
                            <li>• Enter your Gmail address to connect</li>
                            <li>• Requires Google OAuth credentials</li>
                            <li>• Requires OpenAI API key</li>
                            <li>• Gmail OAuth integration</li>
                        </ul>
                    </div>
                    
                    <div className="p-4 border rounded-lg bg-blue-50">
                        <h3 className="font-semibold mb-2 text-blue-800">Google OAuth Setup</h3>
                        <ul className="text-sm space-y-1 text-blue-700">
                            <li>• Create a Google Cloud Project</li>
                            <li>• Enable Gmail API</li>
                            <li>• Configure OAuth consent screen</li>
                            <li>• Add authorized redirect URI</li>
                            <li>• Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET</li>
                        </ul>
                    </div>
                </div>
            </div>

            <EmailDashboard userId={testUserId} />
        </div>
    )
} 