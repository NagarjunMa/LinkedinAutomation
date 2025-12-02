"use client"

import React, { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Mail } from "lucide-react"

interface EmailTabProps {
    userId: string
}

function EmailTab({ userId: _userId }: EmailTabProps) {
    const [settings, setSettings] = useState({
        email_forwarding_enabled: false,
        forwarding_address: '',
        analytics_enabled: true
    })

    return (
        <div className="space-y-6">
            <Card className="premium-card">
                <CardHeader>
                    <CardTitle className="text-cream-50 flex items-center gap-2">
                        <Mail className="h-5 w-5" />
                        Email Tracking
                    </CardTitle>
                    <CardDescription className="text-cream-300">
                        Configure Gmail integration and email forwarding
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="flex items-center justify-between">
                        <div className="space-y-1">
                            <Label className="text-cream-50">Email Forwarding</Label>
                            <p className="text-sm text-cream-400">Forward job-related emails for automatic processing</p>
                        </div>
                        <Switch
                            checked={settings.email_forwarding_enabled}
                            onCheckedChange={(checked) =>
                                setSettings(prev => ({ ...prev, email_forwarding_enabled: checked }))
                            }
                        />
                    </div>

                    <div className="flex items-center justify-between">
                        <div className="space-y-1">
                            <Label className="text-cream-50">Email Analytics</Label>
                            <p className="text-sm text-cream-400">Analyze email patterns and response rates</p>
                        </div>
                        <Switch
                            checked={settings.analytics_enabled}
                            onCheckedChange={(checked) =>
                                setSettings(prev => ({ ...prev, analytics_enabled: checked }))
                            }
                        />
                    </div>

                    <div className="pt-4">
                        <Button className="bg-gradient-warm text-white">
                            Save Email Settings
                        </Button>
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}

export default EmailTab