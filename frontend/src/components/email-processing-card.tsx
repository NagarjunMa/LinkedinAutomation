"use client"

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Mail, CheckCircle, AlertCircle, TrendingUp, Clock } from 'lucide-react'
import { emailScanningApi, EmailScanMetrics } from '@/lib/api/email-scanning-api'

interface EmailProcessingCardProps {
    userId: string
}

export function EmailProcessingCard({ userId }: EmailProcessingCardProps) {
    const [metrics, setMetrics] = useState<EmailScanMetrics | null>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const fetchMetrics = async () => {
            try {
                const data = await emailScanningApi.getPerformanceMetrics(userId, 7)
                setMetrics(data)
            } catch (error) {
                console.error('Failed to fetch email metrics:', error)
            } finally {
                setLoading(false)
            }
        }

        fetchMetrics()
        // Refresh every 30 seconds
        const interval = setInterval(fetchMetrics, 30000)
        return () => clearInterval(interval)
    }, [userId])

    if (loading) {
        return (
            <Card className="premium-card animate-pulse">
                <CardHeader>
                    <CardTitle className="text-cream-50">Email Processing</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="h-32 bg-primary-800 rounded"></div>
                </CardContent>
            </Card>
        )
    }

    if (!metrics) {
        return (
            <Card className="premium-card">
                <CardHeader>
                    <CardTitle className="text-cream-50">Email Processing</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="text-cream-400">No data available</div>
                </CardContent>
            </Card>
        )
    }

    const getProcessingStatusColor = (status: string) => {
        switch (status) {
            case 'processing':
                return 'text-orange-400'
            case 'error':
                return 'text-red-400'
            default:
                return 'text-green-400'
        }
    }

    const getProcessingStatusIcon = (status: string) => {
        switch (status) {
            case 'processing':
                return <Clock className="h-4 w-4" />
            case 'error':
                return <AlertCircle className="h-4 w-4" />
            default:
                return <CheckCircle className="h-4 w-4" />
        }
    }

    return (
        <Card className="premium-card">
            <CardHeader>
                <CardTitle className="text-cream-50 flex items-center justify-between">
                    <span className="flex items-center gap-2">
                        <Mail className="h-5 w-5" />
                        Email Processing
                    </span>
                    <div className="flex items-center gap-2">
                        <div className={`flex items-center gap-1 ${getProcessingStatusColor(metrics.processing_status)}`}>
                            {getProcessingStatusIcon(metrics.processing_status)}
                            <span className="text-sm capitalize">{metrics.processing_status}</span>
                        </div>
                    </div>
                </CardTitle>
                <CardDescription className="text-cream-300">
                    Automated email processing statistics
                </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
                {/* Main Metrics */}
                <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                        <div className="flex items-center gap-2">
                            <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                            <span className="text-sm text-cream-400">Emails Sent</span>
                        </div>
                        <div className="text-2xl font-bold text-green-400">{metrics.emails_sent}</div>
                    </div>

                    <div className="space-y-2">
                        <div className="flex items-center gap-2">
                            <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                            <span className="text-sm text-cream-400">Emails Processed</span>
                        </div>
                        <div className="text-2xl font-bold text-blue-400">{metrics.emails_processed}</div>
                    </div>
                </div>

                {/* Weekly Change */}
                <div className="flex items-center gap-2">
                    <TrendingUp className="h-4 w-4 text-green-400" />
                    <span className="text-sm text-green-400">
                        +{metrics.weekly_change_percentage}% vs last week
                    </span>
                </div>

                {/* Processing Status */}
                <div className="bg-primary-800 rounded-lg p-3">
                    <div className="flex items-center gap-2 mb-2">
                        <div className={`w-2 h-2 rounded-full ${metrics.processing_status === 'processing' ? 'bg-orange-400' :
                                metrics.processing_status === 'error' ? 'bg-red-400' : 'bg-green-400'
                            }`}></div>
                        <span className="text-sm font-medium text-cream-50">Email Processing</span>
                    </div>
                    <div className="text-sm text-cream-300">
                        {metrics.processing_status === 'processing' ? 'Processing emails automatically...' :
                            metrics.processing_status === 'error' ? 'Error in processing - check logs' :
                                'System running smoothly'}
                    </div>
                </div>

                {/* Additional Stats */}
                <div className="grid grid-cols-2 gap-4 pt-2 border-t border-primary-600">
                    <div className="text-center">
                        <div className="text-lg font-semibold text-cream-50">{metrics.status_updates_made}</div>
                        <div className="text-xs text-cream-400">Status Updates</div>
                    </div>
                    <div className="text-center">
                        <div className="text-lg font-semibold text-orange-400">{metrics.urgent_emails_found}</div>
                        <div className="text-xs text-cream-400">Urgent Emails</div>
                    </div>
                </div>
            </CardContent>
        </Card>
    )
}
