"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Loader2, Mail, Eye, CheckCircle, AlertCircle, Calendar, Building } from 'lucide-react'
import { emailAgentApi } from '@/app/lib/api'

interface EmailDashboardProps {
    userId: string
}

interface EmailSummary {
    connected: boolean
    last_sync?: string
    total_processed: number
    recent_count: number
    needs_review: number
    by_type: Record<string, number>
}

interface EmailEvent {
    id: number
    sender_email: string
    sender_name: string
    subject: string
    email_type: string
    confidence_score: number
    company_name: string
    email_received_at: string
    created_at: string
    needs_review: boolean
    status_updated: boolean
    matched_job_id?: number
    ai_data: any
}

const emailTypeColors = {
    rejection: 'destructive',
    interview: 'default',
    offer: 'default',
    update: 'secondary',
    confirmation: 'secondary',
    unknown: 'outline'
} as const

const emailTypeIcons = {
    rejection: AlertCircle,
    interview: Calendar,
    offer: CheckCircle,
    update: Eye,
    confirmation: CheckCircle,
    unknown: Eye
}

export function EmailDashboard({ userId }: EmailDashboardProps) {
    const [summary, setSummary] = useState<EmailSummary | null>(null)
    const [events, setEvents] = useState<EmailEvent[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [selectedType, setSelectedType] = useState<string>('all')

    useEffect(() => {
        fetchData()
    }, [userId])

    const fetchData = async () => {
        setLoading(true)
        try {
            const [summaryRes, eventsRes] = await Promise.all([
                emailAgentApi.getEmailSummary(userId),
                emailAgentApi.getEmailEvents(userId)
            ])

            setSummary(summaryRes)
            setEvents(eventsRes)
            setError(null)
        } catch (err: any) {
            console.error('Failed to fetch email data:', err)
            setError(err.message || 'Failed to fetch email data')
        } finally {
            setLoading(false)
        }
    }

    const markAsReviewed = async (eventId: number) => {
        try {
            await emailAgentApi.markEventReviewed(eventId)
            // Refresh events to update the UI
            const response = await emailAgentApi.getEmailEvents(userId)
            setEvents(response)
        } catch (err: any) {
            console.error('Failed to mark as reviewed:', err)
        }
    }

    const filteredEvents = selectedType === 'all'
        ? events
        : events.filter(event => event.email_type === selectedType)

    if (loading) {
        return (
            <div className="flex items-center justify-center p-8">
                <Loader2 className="h-8 w-8 animate-spin" />
                <span className="ml-2">Loading email data...</span>
            </div>
        )
    }

    if (error) {
        return (
            <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
            </Alert>
        )
    }

    if (!summary?.connected) {
        return (
            <Alert>
                <Mail className="h-4 w-4" />
                <AlertDescription>
                    Please connect your Gmail account to view email analytics.
                </AlertDescription>
            </Alert>
        )
    }

    return (
        <div className="space-y-6">
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Total Processed</CardTitle>
                        <Mail className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{summary.total_processed}</div>
                        <p className="text-xs text-muted-foreground">
                            {summary.last_sync ? `Last sync: ${new Date(summary.last_sync).toLocaleDateString()}` : 'Never synced'}
                        </p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Recent Events</CardTitle>
                        <Calendar className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{summary.recent_count}</div>
                        <p className="text-xs text-muted-foreground">Last 10 events</p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Needs Review</CardTitle>
                        <AlertCircle className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{summary.needs_review}</div>
                        <p className="text-xs text-muted-foreground">Low confidence events</p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Email Types</CardTitle>
                        <Eye className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{Object.keys(summary.by_type).length}</div>
                        <p className="text-xs text-muted-foreground">Different categories</p>
                    </CardContent>
                </Card>
            </div>

            {/* Email Events */}
            <Card>
                <CardHeader>
                    <CardTitle>Email Events</CardTitle>
                    <CardDescription>
                        Recent job application emails and their classifications
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <Tabs value={selectedType} onValueChange={setSelectedType}>
                        <TabsList>
                            <TabsTrigger value="all">All ({events.length})</TabsTrigger>
                            {Object.entries(summary.by_type).map(([type, count]) => (
                                <TabsTrigger key={type} value={type}>
                                    {type.charAt(0).toUpperCase() + type.slice(1)} ({count})
                                </TabsTrigger>
                            ))}
                        </TabsList>

                        <TabsContent value={selectedType} className="space-y-4">
                            {filteredEvents.length === 0 ? (
                                <div className="text-center py-8 text-muted-foreground">
                                    No email events found for this category.
                                </div>
                            ) : (
                                <div className="space-y-4">
                                    {filteredEvents.map((event) => {
                                        const IconComponent = emailTypeIcons[event.email_type as keyof typeof emailTypeIcons] || Eye
                                        return (
                                            <div key={event.id} className="flex items-start space-x-4 p-4 border rounded-lg">
                                                <div className="flex-shrink-0">
                                                    <IconComponent className="h-5 w-5 text-muted-foreground" />
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <div className="flex items-center justify-between">
                                                        <h4 className="text-sm font-medium truncate">{event.subject}</h4>
                                                        <div className="flex items-center space-x-2">
                                                            <Badge variant={emailTypeColors[event.email_type as keyof typeof emailTypeColors] || 'outline'}>
                                                                {event.email_type}
                                                            </Badge>
                                                            {event.needs_review && (
                                                                <Badge variant="destructive">Needs Review</Badge>
                                                            )}
                                                        </div>
                                                    </div>
                                                    <p className="text-sm text-muted-foreground truncate">
                                                        From: {event.sender_name || event.sender_email}
                                                    </p>
                                                    {event.company_name && (
                                                        <p className="text-sm text-muted-foreground truncate">
                                                            Company: {event.company_name}
                                                        </p>
                                                    )}
                                                    <div className="flex items-center justify-between mt-2">
                                                        <p className="text-xs text-muted-foreground">
                                                            {new Date(event.created_at).toLocaleDateString()}
                                                        </p>
                                                        <div className="flex items-center space-x-2">
                                                            <span className="text-xs text-muted-foreground">
                                                                Confidence: {Math.round(event.confidence_score * 100)}%
                                                            </span>
                                                            {event.needs_review && (
                                                                <Button
                                                                    size="sm"
                                                                    variant="outline"
                                                                    onClick={() => markAsReviewed(event.id)}
                                                                >
                                                                    Mark Reviewed
                                                                </Button>
                                                            )}
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        )
                                    })}
                                </div>
                            )}
                        </TabsContent>
                    </Tabs>
                </CardContent>
            </Card>
        </div>
    )
} 