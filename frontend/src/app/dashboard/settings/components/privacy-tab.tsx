"use client"

import React, { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Shield, Settings } from "lucide-react"

interface PrivacyTabProps {
    userId: string
}

function PrivacyTab({ userId }: PrivacyTabProps) {
    const [settings, setSettings] = useState({
        data_retention_days: 365,
        analytics_enabled: true,
        profile_visibility: 'private'
    })

    return (
        <div className="space-y-6">
            <Card className="premium-card">
                <CardHeader>
                    <CardTitle className="text-cream-50 flex items-center gap-2">
                        <Shield className="h-5 w-5" />
                        Privacy Settings
                    </CardTitle>
                    <CardDescription className="text-cream-300">
                        Control your data privacy and retention settings
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="flex items-center justify-between">
                        <div className="space-y-1">
                            <Label className="text-cream-50">Data Retention</Label>
                            <p className="text-sm text-cream-400">How long to keep your data (days)</p>
                        </div>
                        <div className="text-cream-50">
                            {settings.data_retention_days} days
                        </div>
                    </div>

                    <div className="flex items-center justify-between">
                        <div className="space-y-1">
                            <Label className="text-cream-50">Analytics</Label>
                            <p className="text-sm text-cream-400">Allow analytics to improve the service</p>
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
                            Save Privacy Settings
                        </Button>
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}

export default PrivacyTab