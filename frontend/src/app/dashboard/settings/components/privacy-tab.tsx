"use client"

import React, { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Shield } from "lucide-react"
import { profileApi } from '@/app/lib/api/profile'
import { useAuth } from '@/contexts/auth-context'

interface PrivacyTabProps {
    userId: string
}

function PrivacyTab({ userId }: PrivacyTabProps) {
    const { isCurrentUser } = useAuth()
    const [saved, setSaved] = useState<boolean | 'unknown' | null>(null)
    const [analytics, setAnalytics] = useState(false)
    const [retentionDays, setRetentionDays] = useState<number | null>(null)
    const [saving, setSaving] = useState(false)
    const [message, setMessage] = useState<{ text: string; error?: boolean } | null>(null)

    useEffect(() => {
        const controller = new AbortController()
        async function loadSettings() {
            try {
                const settings = await profileApi.getSettings(userId, controller.signal)
                if (controller.signal.aborted) return
                if (settings && settings.user_id !== userId) throw new Error('Invalid privacy settings')

                // Match the API default for an absent row; let the user resolve legacy values explicitly.
                const value = settings === null || settings.analytics_enabled === 'enabled'
                    ? true
                    : settings.analytics_enabled === 'disabled' ? false : 'unknown'
                setSaved(value)
                setAnalytics(value === true)
                setRetentionDays(settings === null ? 365 : settings.data_retention_days ?? null)
            } catch {
                if (!controller.signal.aborted) {
                    setMessage({ text: 'Could not load privacy settings. Reload to try again.', error: true })
                }
            }
        }
        void loadSettings()
        return () => controller.abort()
    }, [userId])

    async function saveSettings() {
        if (saved === null || saved === analytics || saving || !isCurrentUser(userId)) return
        setSaving(true)
        setMessage(null)
        try {
            const value = analytics ? 'enabled' : 'disabled'
            const settings = await profileApi.saveAnalytics(userId, value)
            if (!isCurrentUser(userId)) return
            if (settings.user_id !== userId || settings.analytics_enabled !== value) {
                throw new Error('Privacy settings were not confirmed')
            }
            setSaved(analytics)
            setRetentionDays(settings.data_retention_days ?? null)
            setMessage({ text: 'Privacy settings saved.' })
        } catch {
            if (isCurrentUser(userId)) setMessage({ text: 'Could not save privacy settings. Try again.', error: true })
        } finally {
            setSaving(false)
        }
    }

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
                            {retentionDays === null ? '—' : `${retentionDays} days`}
                        </div>
                    </div>

                    <div className="flex items-center justify-between">
                        <div className="space-y-1">
                            <Label htmlFor="privacy-analytics" className="text-foreground">Analytics</Label>
                            <p className="text-sm text-muted-foreground">Allow analytics to improve the service</p>
                        </div>
                        <Switch
                            id="privacy-analytics"
                            checked={analytics}
                            disabled={saved === null || saving}
                            onCheckedChange={(checked) => {
                                setAnalytics(checked)
                                setMessage(null)
                            }}
                        />
                    </div>

                    <div className="pt-4">
                        <Button
                            onClick={saveSettings}
                            disabled={saved === null || saved === analytics || saving}
                            className="bg-primary text-primary-foreground hover:bg-primary/90"
                        >
                            {saving ? 'Saving…' : 'Save Privacy Settings'}
                        </Button>
                        {saved === 'unknown' && !message && (
                            <p className="mt-2 text-sm text-muted-foreground">
                                There is no recognized analytics preference. Choose a setting and save it.
                            </p>
                        )}
                        {message && (
                            <p className="mt-2 text-sm" role={message.error ? 'alert' : 'status'}>{message.text}</p>
                        )}
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}

export default PrivacyTab