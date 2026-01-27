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
            <Card className="premium-card bg-card border-border">
                <CardHeader>
                    <CardTitle className="text-foreground flex items-center gap-2">
                        <Mail className="h-5 w-5" />
                        Email Tracking
                    </CardTitle>
                    <CardDescription className="text-muted-foreground">
                        Configure Gmail integration and email forwarding
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="flex items-center justify-between">
                        <div className="space-y-1">
                            <Label className="text-foreground">Email Forwarding</Label>
                            <p className="text-sm text-muted-foreground">Forward job-related emails for automatic processing</p>
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
                            <Label className="text-foreground">Email Analytics</Label>
                            <p className="text-sm text-muted-foreground">Analyze email patterns and response rates</p>
                        </div>
                        <Switch
                            checked={settings.analytics_enabled}
                            onCheckedChange={(checked) =>
                                setSettings(prev => ({ ...prev, analytics_enabled: checked }))
                            }
                        />
                    </div>

                    <div className="pt-4">
                        <Button className="bg-primary text-primary-foreground hover:bg-primary/90">
                            Save Email Settings
                        </Button>
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}

export default EmailTab