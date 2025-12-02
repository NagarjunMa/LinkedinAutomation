"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Mail, Send, CheckCircle, Clock } from "lucide-react"
import { cn } from "@/lib/utils"

interface EmailStatsCardProps {
    title: string
    emailsSent: number
    emailsProcessed: number
    change: string
    changeType: "increase" | "decrease"
}

export function EmailStatsCard({ title, emailsSent, emailsProcessed, change, changeType }: EmailStatsCardProps) {
    return (
        <Card className="premium-card hover:scale-105 transition-all duration-300 group h-full flex flex-col">
            <CardHeader className="pb-3 flex-shrink-0">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-cream-50 text-lg group-hover:text-accent-400 transition-colors">{title}</CardTitle>
                    <div className="flex items-center space-x-2">
                        <Mail className="h-4 w-4 text-accent-400" />
                    </div>
                </div>
            </CardHeader>
            <CardContent className="space-y-4 flex-1 flex flex-col">
                {/* Email Stats */}
                <div className="space-y-3">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                            <Send className="h-4 w-4 text-green-400" />
                            <span className="text-sm text-cream-300">Emails Sent</span>
                        </div>
                        <span className="text-2xl font-bold text-green-400">{emailsSent}</span>
                    </div>

                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                            <CheckCircle className="h-4 w-4 text-blue-400" />
                            <span className="text-sm text-cream-300">Emails Processed</span>
                        </div>
                        <span className="text-2xl font-bold text-blue-400">{emailsProcessed}</span>
                    </div>
                </div>

                {/* Change indicator */}
                <div className="flex items-center space-x-2">
                    {changeType === "increase" ? (
                        <CheckCircle className="h-4 w-4 text-green-400" />
                    ) : (
                        <Clock className="h-4 w-4 text-yellow-400" />
                    )}
                    <span className={cn(
                        "text-sm font-medium",
                        changeType === "increase" ? "text-green-400" : "text-yellow-400"
                    )}>
                        {change}
                    </span>
                    <span className="text-sm text-cream-300">vs last week</span>
                </div>

                {/* Processing Status */}
                <div className="mt-4 p-3 bg-primary-700 rounded-lg group-hover:bg-primary-600 transition-colors duration-300">
                    <div className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-accent-400 rounded-full animate-pulse group-hover:bg-accent-300"></div>
                        <span className="text-sm text-cream-200 group-hover:text-cream-50 transition-colors">Email Processing</span>
                    </div>
                    <p className="text-xs text-cream-300 mt-1 group-hover:text-cream-200 transition-colors">
                        {emailsProcessed > 0 ? "Processing emails automatically..." : "No emails to process"}
                    </p>
                </div>
            </CardContent>
        </Card>
    )
}
