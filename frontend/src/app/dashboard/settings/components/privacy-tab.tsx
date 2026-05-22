"use client"

import React, { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Shield } from "lucide-react"

interface PrivacyTabProps {
    userId: string
}

function PrivacyTab({ userId: _userId }: PrivacyTabProps) {
    const [settings, setSettings] = useState({
        data_retention_days: 365,
        analytics_enabled: true,
        profile_visibility: 'private'
    })

    return (
        <div className="space-y-6">
            <Card className="premium-card bg-card border-border">
                <CardHeader>
                    <CardTitle className="text-foreground flex items-center gap-2">
                        <Shield className="h-5 w-5" />
                        Privacy Settings
                    </CardTitle>
                    <CardDescription className="text-muted-foreground">
                        Control how long Prism Pro retains your resume data and evaluation history. Your data is never shared with third parties. Prism Pro is Google OAuth verified and complies with Google&apos;s Limited Use Policy.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="flex items-center justify-between">
                        <div className="space-y-1">
                            <Label className="text-foreground">Data Retention</Label>
                            <p className="text-sm text-muted-foreground">How long to keep your data (days)</p>
                        </div>
                        <div className="text-foreground">
                            {settings.data_retention_days} days
                        </div>
                    </div>

                    <div className="flex items-center justify-between">
                        <div className="space-y-1">
                            <Label className="text-foreground">Analytics</Label>
                            <p className="text-sm text-muted-foreground">Allow analytics to improve the service</p>
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
                            Save Privacy Settings
                        </Button>
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}

export default PrivacyTab