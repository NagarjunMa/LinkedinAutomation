"use client"

import React, { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Bell } from "lucide-react"

interface NotificationsTabProps {
    userId: string
}

function NotificationsTab({ userId: _userId }: NotificationsTabProps) {
    const [settings, setSettings] = useState({
        application_updates: true,
        interview_reminders: true,
        weekly_digest: true,
        referral_responses: true
    })

    return (
        <div className="space-y-6">
            <Card className="premium-card bg-card border-border">
                <CardHeader>
                    <CardTitle className="text-foreground flex items-center gap-2">
                        <Bell className="h-5 w-5" />
                        Notification Preferences
                    </CardTitle>
                    <CardDescription className="text-muted-foreground">
                        Configure how you receive notifications
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="flex items-center justify-between">
                        <div className="space-y-1">
                            <Label className="text-foreground">Application Updates</Label>
                            <p className="text-sm text-muted-foreground">Get notified when application status changes</p>
                        </div>
                        <Switch
                            checked={settings.application_updates}
                            onCheckedChange={(checked) =>
                                setSettings(prev => ({ ...prev, application_updates: checked }))
                            }
                        />
                    </div>

                    <div className="flex items-center justify-between">
                        <div className="space-y-1">
                            <Label className="text-foreground">Interview Reminders</Label>
                            <p className="text-sm text-muted-foreground">Reminders for upcoming interviews</p>
                        </div>
                        <Switch
                            checked={settings.interview_reminders}
                            onCheckedChange={(checked) =>
                                setSettings(prev => ({ ...prev, interview_reminders: checked }))
                            }
                        />
                    </div>

                    <div className="flex items-center justify-between">
                        <div className="space-y-1">
                            <Label className="text-foreground">Weekly Digest</Label>
                            <p className="text-sm text-muted-foreground">Weekly summary of your job search activity</p>
                        </div>
                        <Switch
                            checked={settings.weekly_digest}
                            onCheckedChange={(checked) =>
                                setSettings(prev => ({ ...prev, weekly_digest: checked }))
                            }
                        />
                    </div>

                    <div className="flex items-center justify-between">
                        <div className="space-y-1">
                            <Label className="text-foreground">Referral Responses</Label>
                            <p className="text-sm text-muted-foreground">Notifications for referral email responses</p>
                        </div>
                        <Switch
                            checked={settings.referral_responses}
                            onCheckedChange={(checked) =>
                                setSettings(prev => ({ ...prev, referral_responses: checked }))
                            }
                        />
                    </div>

                    <div className="pt-4">
                        <Button className="bg-primary text-primary-foreground hover:bg-primary/90">
                            Save Notification Settings
                        </Button>
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}

export default NotificationsTab