"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription } from "@/components/ui/alert"
import {
    TrendingUp,
    TrendingDown,
    Activity,
    AlertCircle,
    RefreshCw,
    ExternalLink,
    BarChart3,
    Calendar
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { analyticsAPI, TrendAnalysis, isInsufficientDataError, isAnalyticsAPIError } from "@/lib/analytics-api"
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

interface ApplicationTrendChartProps {
    title?: string
    className?: string
    showActions?: boolean
    days?: number
}

export function ApplicationTrendChart({
    title = "Application Trends",
    className,
    showActions = true,
    days = 30
}: ApplicationTrendChartProps) {
    const router = useRouter()
    const [trendData, setTrendData] = useState<TrendAnalysis | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [isRefreshing, setIsRefreshing] = useState(false)
    const [selectedPeriod, setSelectedPeriod] = useState(days)

    const fetchTrendData = async (period: number = selectedPeriod) => {
        try {
            setError(null)
            const data = await analyticsAPI.getTrends(period)
            setTrendData(data)
        } catch (err) {
            if (isInsufficientDataError(err)) {
                setError("Insufficient data")
            } else if (isAnalyticsAPIError(err)) {
                setError(err.message)
            } else {
                setError("Failed to load trend data")
            }
        } finally {
            setLoading(false)
            setIsRefreshing(false)
        }
    }

    const handleRefresh = async () => {
        setIsRefreshing(true)
        await fetchTrendData()
    }

    const handlePeriodChange = async (newPeriod: number) => {
        setSelectedPeriod(newPeriod)
        setLoading(true)
        await fetchTrendData(newPeriod)
    }

    useEffect(() => {
        fetchTrendData()
    }, [])

    if (loading) {
        return <ApplicationTrendChartSkeleton title={title} className={className} />
    }

    if (error === "Insufficient data") {
        return <InsufficientDataCard title={title} className={className} onRefresh={handleRefresh} />
    }

    if (error) {
        return <ErrorCard title={title} className={className} error={error} onRefresh={handleRefresh} />
    }

    if (!trendData) {
        return <ErrorCard title={title} className={className} error="No data available" onRefresh={handleRefresh} />
    }

    // Format data for the chart
    const chartData = (trendData.data_points || []).map(point => ({
        date: new Date(point.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        applications: point.applications,
        responses: point.responses || 0,
        fullDate: point.date
    }))

    const getTrendColor = (direction: string) => {
        switch (direction) {
            case 'up': return 'text-green-400'
            case 'down': return 'text-red-400'
            default: return 'text-cream-300'
        }
    }

    const getTrendIcon = (direction: string) => {
        switch (direction) {
            case 'up': return TrendingUp
            case 'down': return TrendingDown
            default: return Activity
        }
    }

    const TrendIcon = getTrendIcon(trendData.trend_direction)

    return (
        <Card className={cn(
            "premium-card hover:scale-105 transition-all duration-300 group max-h-[600px] flex flex-col",
            className
        )}>
            <CardHeader className="pb-3 shrink-0">
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                        <BarChart3 className="h-5 w-5 text-accent-400 group-hover:text-accent-300 transition-colors" />
                        <CardTitle className="text-cream-50 text-lg group-hover:text-accent-400 transition-colors">
                            {title}
                        </CardTitle>
                    </div>
                    {showActions && (
                        <div className="flex items-center space-x-2">
                            <div className="flex items-center space-x-1">
                                {[7, 30, 90].map((period) => (
                                    <Button
                                        key={period}
                                        variant={selectedPeriod === period ? "secondary" : "ghost"}
                                        size="sm"
                                        onClick={() => handlePeriodChange(period)}
                                        className={cn(
                                            "text-xs px-2 py-1",
                                            selectedPeriod === period
                                                ? "bg-accent-500 text-white"
                                                : "text-cream-300 hover:text-cream-50"
                                        )}
                                    >
                                        {period}d
                                    </Button>
                                ))}
                            </div>
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={handleRefresh}
                                disabled={isRefreshing}
                                className="text-cream-300 hover:text-cream-50 text-xs px-2 py-1"
                            >
                                {isRefreshing ? (
                                    <RefreshCw className="h-3 w-3 animate-spin" />
                                ) : (
                                    "Refresh"
                                )}
                            </Button>
                        </div>
                    )}
                </div>

                {/* Trend Summary */}
                <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center space-x-4">
                        <div className="flex items-center space-x-1">
                            <TrendIcon className={cn("h-4 w-4", getTrendColor(trendData.trend_direction))} />
                            <span className={cn("font-medium capitalize", getTrendColor(trendData.trend_direction))}>
                                {trendData.trend_direction} trend
                            </span>
                        </div>
                        <Badge className="bg-primary-700 text-cream-300 border-primary-500 text-xs">
                            {trendData.average_per_week} apps/week
                        </Badge>
                    </div>
                    <div className="text-cream-400 text-xs">
                        {trendData.total_applications} total applications
                    </div>
                </div>
            </CardHeader>

            <CardContent className="flex-1 flex flex-col min-h-0">
                {/* Chart Container */}
                <div className="h-64 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart
                            data={chartData}
                            margin={{
                                top: 10,
                                right: 10,
                                left: 0,
                                bottom: 20,
                            }}
                        >
                            <defs>
                                <linearGradient id="applicationGradient" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="rgb(249, 115, 22)" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="rgb(249, 115, 22)" stopOpacity={0.05} />
                                </linearGradient>
                                <linearGradient id="responseGradient" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="rgb(34, 197, 94)" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="rgb(34, 197, 94)" stopOpacity={0.05} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                            <XAxis
                                dataKey="date"
                                axisLine={false}
                                tickLine={false}
                                tick={{ fill: 'rgb(203, 213, 225)', fontSize: 12 }}
                                interval="preserveStartEnd"
                            />
                            <YAxis
                                axisLine={false}
                                tickLine={false}
                                tick={{ fill: 'rgb(203, 213, 225)', fontSize: 12 }}
                                width={30}
                            />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: 'rgb(51, 65, 85)',
                                    border: '1px solid rgb(100, 116, 139)',
                                    borderRadius: '8px',
                                    color: 'rgb(248, 250, 252)'
                                }}
                                labelStyle={{ color: 'rgb(248, 250, 252)' }}
                                formatter={(value: number, name: string) => [
                                    value,
                                    name === 'applications' ? 'Applications' : 'Responses'
                                ]}
                                labelFormatter={(label) => `Date: ${label}`}
                            />
                            <Area
                                type="monotone"
                                dataKey="applications"
                                stroke="rgb(249, 115, 22)"
                                strokeWidth={2}
                                fill="url(#applicationGradient)"
                                dot={{ fill: 'rgb(249, 115, 22)', strokeWidth: 2, r: 3 }}
                                activeDot={{ r: 5, stroke: 'rgb(249, 115, 22)', strokeWidth: 2 }}
                            />
                            {chartData.some(d => d.responses > 0) && (
                                <Area
                                    type="monotone"
                                    dataKey="responses"
                                    stroke="rgb(34, 197, 94)"
                                    strokeWidth={2}
                                    fill="url(#responseGradient)"
                                    dot={{ fill: 'rgb(34, 197, 94)', strokeWidth: 2, r: 3 }}
                                    activeDot={{ r: 5, stroke: 'rgb(34, 197, 94)', strokeWidth: 2 }}
                                />
                            )}
                        </AreaChart>
                    </ResponsiveContainer>
                </div>

                {/* Stats Summary */}
                <div className="grid grid-cols-3 gap-3 mt-4 pt-3 border-t border-primary-600">
                    <div className="text-center">
                        <div className="text-lg font-bold text-cream-50">{trendData.total_applications}</div>
                        <div className="text-xs text-cream-300">Total Apps</div>
                    </div>
                    <div className="text-center">
                        <div className="text-lg font-bold text-accent-400">{trendData.average_per_week}</div>
                        <div className="text-xs text-cream-300">Per Week</div>
                    </div>
                    <div className="text-center">
                        <div className="text-lg font-bold text-gold-400">{selectedPeriod}</div>
                        <div className="text-xs text-cream-300">Days Period</div>
                    </div>
                </div>

                {/* Action Button */}
                {showActions && (
                    <div className="mt-4">
                        <Button
                            className="w-full bg-primary-700 hover:bg-primary-600 text-cream-50 border-primary-500 hover:border-accent-500 transition-all duration-200 group/btn"
                            onClick={() => router.push('/dashboard/analytics')}
                        >
                            <div className="flex items-center space-x-2">
                                <Calendar className="h-4 w-4 group-hover/btn:text-accent-400 transition-colors" />
                                <span>View Detailed Analytics</span>
                                <ExternalLink className="h-3 w-3 group-hover/btn:text-accent-400 transition-colors" />
                            </div>
                        </Button>
                    </div>
                )}
            </CardContent>
        </Card>
    )
}

function ApplicationTrendChartSkeleton({ title, className }: { title: string; className?: string }) {
    return (
        <Card className={cn(
            "premium-card h-full flex flex-col",
            className
        )}>
            <CardHeader className="pb-3 shrink-0">
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                        <BarChart3 className="h-5 w-5 text-accent-400" />
                        <CardTitle className="text-cream-50 text-lg">{title}</CardTitle>
                    </div>
                    <div className="flex space-x-1">
                        {[1, 2, 3].map((i) => (
                            <Skeleton key={i} className="h-6 w-8 bg-primary-700" />
                        ))}
                    </div>
                </div>
                <div className="flex items-center justify-between">
                    <Skeleton className="h-4 w-24 bg-primary-700" />
                    <Skeleton className="h-4 w-32 bg-primary-700" />
                </div>
            </CardHeader>

            <CardContent className="flex-1 flex flex-col">
                <Skeleton className="flex-1 bg-primary-700 rounded-lg" />

                <div className="grid grid-cols-3 gap-3 mt-4 pt-3 border-t border-primary-600">
                    {Array.from({ length: 3 }).map((_, i) => (
                        <div key={i} className="text-center space-y-1">
                            <Skeleton className="h-6 w-8 mx-auto bg-primary-700" />
                            <Skeleton className="h-3 w-12 mx-auto bg-primary-700" />
                        </div>
                    ))}
                </div>

                <Skeleton className="h-10 w-full mt-4 bg-primary-700" />
            </CardContent>
        </Card>
    )
}

function InsufficientDataCard({
    title,
    className,
    onRefresh
}: {
    title: string;
    className?: string;
    onRefresh: () => void
}) {
    return (
        <Card className={cn(
            "premium-card h-full flex flex-col",
            className
        )}>
            <CardHeader className="pb-3 shrink-0">
                <div className="flex items-center space-x-2">
                    <BarChart3 className="h-5 w-5 text-accent-400" />
                    <CardTitle className="text-cream-50 text-lg">{title}</CardTitle>
                </div>
            </CardHeader>

            <CardContent className="flex-1 flex flex-col items-center justify-center space-y-4">
                <Alert className="border-gold-500/20 bg-gold-500/10">
                    <AlertCircle className="h-4 w-4 text-gold-400" />
                    <AlertDescription className="text-cream-200">
                        No application data found for trend analysis. Start applying to jobs to see your progress over time.
                    </AlertDescription>
                </Alert>

                <div className="text-center space-y-2">
                    <div className="text-6xl">📈</div>
                    <p className="text-sm text-cream-300">
                        Your application trends will appear here once you start applying to jobs.
                    </p>
                </div>

                <Button
                    onClick={onRefresh}
                    className="bg-gold-500 hover:bg-gold-400 text-white"
                >
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Check Again
                </Button>
            </CardContent>
        </Card>
    )
}

function ErrorCard({
    title,
    className,
    error,
    onRefresh
}: {
    title: string;
    className?: string;
    error: string;
    onRefresh: () => void
}) {
    return (
        <Card className={cn(
            "premium-card h-full flex flex-col",
            className
        )}>
            <CardHeader className="pb-3 shrink-0">
                <div className="flex items-center space-x-2">
                    <BarChart3 className="h-5 w-5 text-accent-400" />
                    <CardTitle className="text-cream-50 text-lg">{title}</CardTitle>
                </div>
            </CardHeader>

            <CardContent className="flex-1 flex flex-col items-center justify-center space-y-4">
                <Alert className="border-red-500/20 bg-red-500/10">
                    <AlertCircle className="h-4 w-4 text-red-400" />
                    <AlertDescription className="text-cream-200">
                        {error}
                    </AlertDescription>
                </Alert>

                <div className="text-center space-y-2">
                    <div className="text-6xl">⚠️</div>
                    <p className="text-sm text-cream-300">
                        Unable to load trend data. Please try again.
                    </p>
                </div>

                <Button
                    onClick={onRefresh}
                    className="bg-red-500 hover:bg-red-400 text-white"
                >
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Retry
                </Button>
            </CardContent>
        </Card>
    )
}
