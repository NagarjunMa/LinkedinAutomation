"use client"

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Badge } from "@/components/ui/badge"
import { useToast } from "@/components/ui/use-toast"
import {
    Clock,
    Mail,
    Settings,
    CheckCircle,
    AlertCircle,
    Calendar,
    Zap
} from "lucide-react"
import { formatDistanceToNow } from 'date-fns'
import { emailScanningApi, EmailScanStatus } from '@/lib/api/email-scanning-api'

interface LocalEmailScanSettings {
    frequency: string
    scan_time: string
    timezone: string
    email_tracking_enabled: boolean
}

interface EmailScanningSettingsProps {
    userId: string
}

function EmailScanningSettings({ userId }: EmailScanningSettingsProps) {
    const { toast } = useToast()
    const [settings, setSettings] = useState<LocalEmailScanSettings>({
        frequency: 'daily',
        scan_time: '03:00',
        timezone: 'America/New_York',
        email_tracking_enabled: true
    })
    const [scanStatus, setScanStatus] = useState<EmailScanStatus | null>(null)
    const [_loading, _setLoading] = useState(false)
    const [saving, setSaving] = useState(false)

    // Load settings and status on mount
    useEffect(() => {
        loadSettings()
        loadScanStatus()
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [userId])

    const loadSettings = async () => {
        try {
            const data = await emailScanningApi.getSettings(userId)
            setSettings({
                frequency: data.email_scan_frequency,
                scan_time: data.email_scan_time.substring(0, 5), // Convert "HH:MM:SS" to "HH:MM"
                timezone: data.email_scan_timezone,
                email_tracking_enabled: data.email_tracking_enabled
            })
            setScanStatus(data)
        } catch (error) {
            console.error('Failed to load settings:', error)
            toast({
                title: "Error",
                description: "Failed to load email scanning settings",
                variant: "destructive",
            })
        }
    }

    const loadScanStatus = async () => {
        try {
            const data = await emailScanningApi.getScanStatus(userId)
            setScanStatus(data)
        } catch (error) {
            console.error('Failed to load scan status:', error)
        }
    }

    const handleSaveSettings = async () => {
        setSaving(true)
        try {
            await emailScanningApi.updateSettings(userId, {
                email_scan_frequency: settings.frequency as 'daily' | 'twice_daily' | 'weekly',
                email_scan_time: `${settings.scan_time}:00`,
                email_scan_timezone: settings.timezone,
                email_tracking_enabled: settings.email_tracking_enabled
            })

            toast({
                title: "Settings Saved",
                description: "Email scanning preferences updated successfully",
            })
            await loadScanStatus()
        } catch {
            toast({
                title: "Error",
                description: "Failed to save email scanning settings",
                variant: "destructive",
            })
        } finally {
            setSaving(false)
        }
    }

    const formatTime = (hour: number) => {
        const period = hour >= 12 ? 'PM' : 'AM'
        const displayHour = hour === 0 ? 12 : hour > 12 ? hour - 12 : hour
        return `${displayHour}:00 ${period}`
    }

    const _getFrequencyDescription = (frequency: string) => {
        const descriptions = {
            daily: "Scan every night for new emails",
            twice_daily: "Morning 6 AM and Night 10 PM",
            weekly: "Every Monday at selected time",
            bi_weekly: "1st and 15th of each month",
            monthly: "1st of each month"
        }
        return descriptions[frequency as keyof typeof descriptions] || ""
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-cream-50 flex items-center gap-2">
                        <Mail className="h-6 w-6" />
                        Email Scanning
                    </h2>
                    <p className="text-cream-300 mt-1">
                        Automatically process forwarded job-related emails
                    </p>
                </div>
                <Badge variant="outline" className="text-accent-400 border-accent-400">
                    <Zap className="h-3 w-3 mr-1" />
                    Automated
                </Badge>
            </div>

            {/* Email Tracking Toggle */}
            <Card className="premium-card">
                <CardHeader>
                    <CardTitle className="text-cream-50 flex items-center gap-2">
                        <Settings className="h-5 w-5" />
                        Email Tracking
                    </CardTitle>
                    <CardDescription className="text-cream-300">
                        Enable automatic processing of forwarded job emails
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="flex items-center justify-between">
                        <div className="space-y-1">
                            <Label htmlFor="email-tracking" className="text-cream-50">
                                Enable Email Tracking
                            </Label>
                            <p className="text-sm text-cream-400">
                                Forward job emails to jobtrack_{userId}@jobflowpro.com
                            </p>
                        </div>
                        <Switch
                            id="email-tracking"
                            checked={settings.email_tracking_enabled}
                            onCheckedChange={(checked) =>
                                setSettings(prev => ({ ...prev, email_tracking_enabled: checked }))
                            }
                        />
                    </div>
                </CardContent>
            </Card>

            {/* Scan Frequency */}
            <Card className="premium-card">
                <CardHeader>
                    <CardTitle className="text-cream-50 flex items-center gap-2">
                        <Calendar className="h-5 w-5" />
                        Scan Frequency
                    </CardTitle>
                    <CardDescription className="text-cream-300">
                        How often to scan for new emails
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <RadioGroup
                        value={settings.frequency}
                        onValueChange={(value) =>
                            setSettings(prev => ({ ...prev, frequency: value }))
                        }
                        className="space-y-3"
                    >
                        <div className="flex items-center space-x-3 p-3 rounded-lg border border-primary-600 hover:bg-primary-800/50 transition-colors">
                            <RadioGroupItem value="daily" id="daily" />
                            <div className="flex-1">
                                <Label htmlFor="daily" className="text-cream-50 font-medium cursor-pointer">
                                    Daily (Recommended)
                                </Label>
                                <p className="text-sm text-cream-400">
                                    Scan every night for new emails
                                </p>
                            </div>
                        </div>

                        <div className="flex items-center space-x-3 p-3 rounded-lg border border-primary-600 hover:bg-primary-800/50 transition-colors">
                            <RadioGroupItem value="twice_daily" id="twice_daily" />
                            <div className="flex-1">
                                <Label htmlFor="twice_daily" className="text-cream-50 font-medium cursor-pointer">
                                    Twice Daily
                                </Label>
                                <p className="text-sm text-cream-400">
                                    Morning 6 AM and Night 10 PM
                                </p>
                            </div>
                        </div>

                        <div className="flex items-center space-x-3 p-3 rounded-lg border border-primary-600 hover:bg-primary-800/50 transition-colors">
                            <RadioGroupItem value="weekly" id="weekly" />
                            <div className="flex-1">
                                <Label htmlFor="weekly" className="text-cream-50 font-medium cursor-pointer">
                                    Weekly
                                </Label>
                                <p className="text-sm text-cream-400">
                                    Every Monday at selected time
                                </p>
                            </div>
                        </div>

                        <div className="flex items-center space-x-3 p-3 rounded-lg border border-primary-600 hover:bg-primary-800/50 transition-colors">
                            <RadioGroupItem value="bi_weekly" id="bi_weekly" />
                            <div className="flex-1">
                                <Label htmlFor="bi_weekly" className="text-cream-50 font-medium cursor-pointer">
                                    Bi-weekly
                                </Label>
                                <p className="text-sm text-cream-400">
                                    1st and 15th of each month
                                </p>
                            </div>
                        </div>

                        <div className="flex items-center space-x-3 p-3 rounded-lg border border-primary-600 hover:bg-primary-800/50 transition-colors">
                            <RadioGroupItem value="monthly" id="monthly" />
                            <div className="flex-1">
                                <Label htmlFor="monthly" className="text-cream-50 font-medium cursor-pointer">
                                    Monthly
                                </Label>
                                <p className="text-sm text-cream-400">
                                    1st of each month
                                </p>
                            </div>
                        </div>
                    </RadioGroup>
                </CardContent>
            </Card>

            {/* Scan Time */}
            <Card className="premium-card">
                <CardHeader>
                    <CardTitle className="text-cream-50 flex items-center gap-2">
                        <Clock className="h-5 w-5" />
                        Preferred Scan Time
                    </CardTitle>
                    <CardDescription className="text-cream-300">
                        Choose when to scan emails in your timezone
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="space-y-2">
                        <Label className="text-cream-50">Scan Time</Label>
                        <Select
                            value={settings.scan_time}
                            onValueChange={(value) =>
                                setSettings(prev => ({ ...prev, scan_time: value }))
                            }
                        >
                            <SelectTrigger className="bg-primary-700 border-primary-600 text-cream-50">
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent className="bg-primary-700 border-primary-600">
                                {Array.from({ length: 24 }, (_, i) => (
                                    <SelectItem key={i} value={`${i.toString().padStart(2, '0')}:00`}>
                                        {formatTime(i)}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                        <p className="text-xs text-cream-400">
                            Emails will be scanned at this time in your timezone ({settings.timezone})
                        </p>
                    </div>
                </CardContent>
            </Card>

            {/* Important Notice */}
            <Card className="premium-card border-gold-500/30 bg-gold-500/10">
                <CardContent className="pt-6">
                    <div className="flex gap-3">
                        <AlertCircle className="h-5 w-5 text-gold-400 flex-shrink-0 mt-0.5" />
                        <div className="text-sm text-cream-200">
                            <strong className="text-gold-400">Important:</strong> Interview invitations are checked every 2 hours regardless
                            of your scan frequency to ensure you never miss time-sensitive opportunities.
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Last Scan Info */}
            <Card className="premium-card">
                <CardHeader>
                    <CardTitle className="text-cream-50 flex items-center gap-2">
                        <CheckCircle className="h-5 w-5" />
                        Scan Status
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    {scanStatus ? (
                        <div className="space-y-3">
                            <div className="flex items-center justify-between">
                                <div className="text-sm text-cream-300">
                                    Last scan: {scanStatus.last_full_scan ?
                                        formatDistanceToNow(new Date(scanStatus.last_full_scan), { addSuffix: true }) :
                                        'Never'
                                    }
                                </div>
                                <div className="flex gap-2">
                                    <Badge variant="outline" className="text-green-400 border-green-400">
                                        {scanStatus.emails_processed_today} processed today
                                    </Badge>
                                    {scanStatus.urgent_emails_found_today > 0 && (
                                        <Badge variant="outline" className="text-orange-400 border-orange-400">
                                            {scanStatus.urgent_emails_found_today} urgent today
                                        </Badge>
                                    )}
                                </div>
                            </div>

                            {scanStatus.next_scheduled_scan && (
                                <div className="text-sm text-cream-400">
                                    Next scan: {new Date(scanStatus.next_scheduled_scan).toLocaleString()}
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="text-sm text-cream-400">
                            No scans completed yet
                        </div>
                    )}

                    <div className="flex gap-2 pt-2">
                        <Button
                            onClick={loadScanStatus}
                            variant="outline"
                            className="border-primary-600 text-cream-50 hover:bg-primary-700"
                        >
                            Refresh Status
                        </Button>
                    </div>
                </CardContent>
            </Card>

            {/* Save Button */}
            <div className="flex justify-end">
                <Button
                    onClick={handleSaveSettings}
                    disabled={saving}
                    className="bg-gradient-warm text-white px-8 py-2"
                >
                    {saving ? "Saving..." : "Save Email Scanning Preferences"}
                </Button>
            </div>
        </div>
    )
}

export default EmailScanningSettings
