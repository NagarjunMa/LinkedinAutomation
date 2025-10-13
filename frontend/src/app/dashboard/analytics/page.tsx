"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Skeleton } from "@/components/ui/skeleton"
import {
    ArrowLeftIcon,
    RefreshCwIcon,
    TrendingUpIcon,
    BarChart3Icon,
    BrainIcon,
    TargetIcon,
    Settings,
    AlertCircle,
    Activity,
    Calendar,
    Award,
    Lightbulb
} from "lucide-react"
import { useRouter } from "next/navigation"
import { cn } from "@/lib/utils"
import { analyticsAPI, FullAnalytics, isInsufficientDataError, isAnalyticsAPIError } from "@/lib/analytics-api"
import { SkillsAnalyticsCard } from "@/components/skills-analytics-card"
import { PreferencesAnalyticsCard } from "@/components/preferences-analytics-card"
import { ApplicationTrendChart } from "@/components/application-trend-chart"

export default function AnalyticsPage() {
    const [analyticsData, setAnalyticsData] = useState<FullAnalytics | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [refreshing, setRefreshing] = useState(false)
    const [selectedPeriod, setSelectedPeriod] = useState(30)
    const router = useRouter()

    const fetchAnalytics = async (days: number = selectedPeriod, forceRefresh: boolean = false) => {
        try {
            setError(null)
            if (!forceRefresh) setLoading(true)

            const data = await analyticsAPI.getFullAnalytics(days, forceRefresh)
            setAnalyticsData(data)
        } catch (err) {
            if (isInsufficientDataError(err)) {
                setError("insufficient_data")
            } else if (isAnalyticsAPIError(err)) {
                setError(err.message)
            } else {
                setError("Failed to load analytics data")
            }
        } finally {
            setLoading(false)
            setRefreshing(false)
        }
    }

    const handleRefresh = async () => {
        setRefreshing(true)
        await fetchAnalytics(selectedPeriod, true)
    }

    const handlePeriodChange = (days: number) => {
        setSelectedPeriod(days)
        fetchAnalytics(days)
    }

    useEffect(() => {
        fetchAnalytics()
    }, [])

    if (loading) {
        return <AnalyticsPageSkeleton />
    }

    if (error === "insufficient_data") {
        return <InsufficientDataPage onRetry={() => fetchAnalytics(selectedPeriod, true)} />
    }

    if (error) {
        return <ErrorPage error={error} onRetry={() => fetchAnalytics(selectedPeriod, true)} />
    }

    if (!analyticsData) {
        return <ErrorPage error="No analytics data available" onRetry={() => fetchAnalytics(selectedPeriod, true)} />
    }

    return (
        <div className="w-full px-4 sm:px-6 py-4 sm:py-6">
            <div className="space-y-4 sm:space-y-6">
                {/* Header */}
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                    <div className="flex items-center gap-4">
                        <Button
                            onClick={() => router.push('/dashboard')}
                            variant="outline"
                            size="sm"
                            className="border-primary-500 text-cream-300 hover:text-cream-50 hover:border-accent-500"
                        >
                            <ArrowLeftIcon className="h-4 w-4" />
                            Back to Dashboard
                        </Button>
                        <div>
                            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-cream-50">Analytics Intelligence</h1>
                            <p className="text-cream-200 text-sm sm:text-base">
                                AI-powered insights from your job application data
                            </p>
                        </div>
                    </div>
                    <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2">
                        <div className="flex items-center space-x-1">
                            {[7, 30, 90].map((days) => (
                                <Button
                                    key={days}
                                    variant={selectedPeriod === days ? "secondary" : "ghost"}
                                    size="sm"
                                    onClick={() => handlePeriodChange(days)}
                                    className={cn(
                                        "text-xs px-2 sm:px-3 py-1",
                                        selectedPeriod === days
                                            ? "bg-accent-500 text-white"
                                            : "text-cream-300 hover:text-cream-50"
                                    )}
                                >
                                    {days} days
                                </Button>
                            ))}
                        </div>
                        <Button
                            onClick={handleRefresh}
                            disabled={refreshing}
                            variant="outline"
                            size="sm"
                            className="border-primary-500 text-cream-300 hover:text-cream-50 hover:border-accent-500"
                        >
                            <RefreshCwIcon className={cn("h-4 w-4 mr-2", refreshing && "animate-spin")} />
                            Refresh
                        </Button>
                    </div>
                </div>

                {/* Analytics Overview Cards */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    <Card className="premium-card hover:scale-105 transition-all duration-300">
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium text-cream-50">Total Applications</CardTitle>
                            <TargetIcon className="h-4 w-4 text-accent-400" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-accent-400">{analyticsData.metadata.total_applications}</div>
                            <p className="text-xs text-cream-300">
                                Last {analyticsData.metadata.analysis_period_days} days
                            </p>
                        </CardContent>
                    </Card>

                    <Card className="premium-card hover:scale-105 transition-all duration-300">
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium text-cream-50">AI Insights</CardTitle>
                            <BrainIcon className="h-4 w-4 text-accent-400" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-gold-400">{analyticsData.insights.length}</div>
                            <p className="text-xs text-cream-300">
                                Actionable recommendations
                            </p>
                        </CardContent>
                    </Card>

                    <Card className="premium-card hover:scale-105 transition-all duration-300">
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium text-cream-50">Skills Tracked</CardTitle>
                            <Activity className="h-4 w-4 text-accent-400" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-green-400">{analyticsData.skills.top_skills.length}</div>
                            <p className="text-xs text-cream-300">
                                In demand skills found
                            </p>
                        </CardContent>
                    </Card>

                    <Card className="premium-card hover:scale-105 transition-all duration-300">
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium text-cream-50">Primary Focus</CardTitle>
                            <Award className="h-4 w-4 text-accent-400" />
                        </CardHeader>
                        <CardContent>
                            <div className="text-lg font-bold text-blue-400">
                                {analyticsData.preferences.job_titles.primary_focus || "Various"}
                            </div>
                            <p className="text-xs text-cream-300">
                                Most applied job type
                            </p>
                        </CardContent>
                    </Card>
                </div>

                {/* Analytics Tabs */}
                <Tabs defaultValue="overview" className="space-y-4">
                    <TabsList className="grid w-full grid-cols-4 bg-primary-800 border-primary-600">
                        <TabsTrigger
                            value="overview"
                            className="data-[state=active]:bg-accent-500 data-[state=active]:text-white text-cream-300"
                        >
                            Overview
                        </TabsTrigger>
                        <TabsTrigger
                            value="skills"
                            className="data-[state=active]:bg-accent-500 data-[state=active]:text-white text-cream-300"
                        >
                            Skills
                        </TabsTrigger>
                        <TabsTrigger
                            value="trends"
                            className="data-[state=active]:bg-accent-500 data-[state=active]:text-white text-cream-300"
                        >
                            Trends
                        </TabsTrigger>
                        <TabsTrigger
                            value="insights"
                            className="data-[state=active]:bg-accent-500 data-[state=active]:text-white text-cream-300"
                        >
                            AI Insights
                        </TabsTrigger>
                    </TabsList>

                    {/* Overview Tab */}
                    <TabsContent value="overview" className="space-y-4">
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            <div className="space-y-6">
                                <SkillsAnalyticsCard showActions={false} />
                                <PreferencesAnalyticsCard showActions={false} />
                            </div>
                            <div className="space-y-6">
                                <ApplicationTrendChart days={selectedPeriod} showActions={false} />

                                {/* Application Behavior Card */}
                                {analyticsData.behavior && (
                                    <Card className="premium-card">
                                        <CardHeader>
                                            <CardTitle className="flex items-center gap-2 text-cream-50">
                                                <Activity className="h-5 w-5 text-accent-400" />
                                                Application Behavior
                                            </CardTitle>
                                        </CardHeader>
                                        <CardContent className="space-y-4">
                                            <div className="grid grid-cols-2 gap-4">
                                                <div className="text-center">
                                                    <div className="text-lg font-bold text-accent-400">
                                                        {analyticsData.behavior.velocity.apps_per_week}
                                                    </div>
                                                    <div className="text-xs text-cream-300">Apps per week</div>
                                                </div>
                                                <div className="text-center">
                                                    <div className="text-lg font-bold text-gold-400">
                                                        {analyticsData.behavior.success_metrics.application_rate.toFixed(1)}%
                                                    </div>
                                                    <div className="text-xs text-cream-300">Success rate</div>
                                                </div>
                                            </div>

                                            {/* Peak Days */}
                                            <div className="space-y-2">
                                                <h4 className="text-sm font-medium text-cream-200">Peak Application Days</h4>
                                                <div className="flex flex-wrap gap-2">
                                                    {analyticsData.behavior.timing_patterns.peak_days.slice(0, 3).map(([day, count], index) => (
                                                        <Badge key={index} className="bg-accent-500/20 text-accent-300 border-accent-500/30">
                                                            {day}: {count} apps
                                                        </Badge>
                                                    ))}
                                                </div>
                                            </div>
                                        </CardContent>
                                    </Card>
                                )}
                            </div>
                        </div>
                    </TabsContent>

                    {/* Skills Tab */}
                    <TabsContent value="skills" className="space-y-4">
                        <SkillsAnalyticsCard className="w-full" />
                    </TabsContent>

                    {/* Trends Tab */}
                    <TabsContent value="trends" className="space-y-4">
                        <ApplicationTrendChart days={selectedPeriod} className="w-full" />
                    </TabsContent>

                    {/* AI Insights Tab */}
                    <TabsContent value="insights" className="space-y-4">
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            {analyticsData.insights.map((insight, index) => (
                                <Card key={index} className="premium-card">
                                    <CardHeader>
                                        <div className="flex items-center justify-between">
                                            <CardTitle className="flex items-center gap-2 text-cream-50">
                                                <Lightbulb className="h-5 w-5 text-accent-400" />
                                                {insight.title}
                                            </CardTitle>
                                            <Badge
                                                className={cn(
                                                    "text-xs",
                                                    insight.priority === "high"
                                                        ? "bg-red-500/20 text-red-300 border-red-500/30"
                                                        : insight.priority === "medium"
                                                            ? "bg-gold-500/20 text-gold-300 border-gold-500/30"
                                                            : "bg-accent-500/20 text-accent-300 border-accent-500/30"
                                                )}
                                            >
                                                {insight.priority} priority
                                            </Badge>
                                        </div>
                                    </CardHeader>
                                    <CardContent className="space-y-3">
                                        <p className="text-sm text-cream-200">{insight.message}</p>

                                        {insight.action && (
                                            <div className="bg-primary-700 rounded-lg p-3">
                                                <h4 className="text-sm font-medium text-cream-200 mb-1">Recommended Action:</h4>
                                                <p className="text-xs text-cream-300">{insight.action}</p>
                                            </div>
                                        )}

                                        {insight.impact && (
                                            <div className="flex items-center justify-between text-xs">
                                                <span className="text-cream-400">Expected Impact:</span>
                                                <Badge className="bg-green-500/20 text-green-300 border-green-500/30">
                                                    {insight.impact}
                                                </Badge>
                                            </div>
                                        )}

                                        <Badge className="bg-primary-700 text-cream-300 border-primary-500 text-xs">
                                            {insight.type.replace('_', ' ')}
                                        </Badge>
                                    </CardContent>
                                </Card>
                            ))}

                            {analyticsData.insights.length === 0 && (
                                <div className="col-span-2 text-center py-12">
                                    <div className="text-6xl mb-4">💡</div>
                                    <h3 className="text-lg font-medium text-cream-200 mb-2">No insights available yet</h3>
                                    <p className="text-sm text-cream-400">
                                        Continue applying to jobs to generate AI-powered insights
                                    </p>
                                </div>
                            )}
                        </div>
                    </TabsContent>
                </Tabs>
            </div>
        </div>
    )
}

// Helper Components
function AnalyticsPageSkeleton() {
    return (
        <div className="w-full px-6 py-6">
            <div className="space-y-6">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Skeleton className="h-9 w-32 bg-primary-700" />
                        <div className="space-y-2">
                            <Skeleton className="h-8 w-64 bg-primary-700" />
                            <Skeleton className="h-4 w-96 bg-primary-700" />
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        <Skeleton className="h-9 w-24 bg-primary-700" />
                        <Skeleton className="h-9 w-24 bg-primary-700" />
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {Array.from({ length: 4 }).map((_, i) => (
                        <Skeleton key={i} className="h-32 bg-primary-700" />
                    ))}
                </div>

                <Skeleton className="h-10 w-full bg-primary-700" />
                <Skeleton className="h-96 w-full bg-primary-700" />
            </div>
        </div>
    )
}

function InsufficientDataPage({ onRetry }: { onRetry: () => void }) {
    return (
        <div className="w-full px-6 py-6">
            <div className="flex items-center justify-center min-h-[60vh]">
                <div className="text-center space-y-6 max-w-md">
                    <div className="text-8xl">📊</div>
                    <div className="space-y-3">
                        <h1 className="text-2xl font-bold text-cream-50">Insufficient Data for Analytics</h1>
                        <p className="text-cream-300">
                            We need at least 3 job applications to generate meaningful analytics insights.
                            Start applying to jobs to unlock powerful AI-driven analytics.
                        </p>
                    </div>

                    <Alert className="border-gold-500/20 bg-gold-500/10 text-left">
                        <AlertCircle className="h-4 w-4 text-gold-400" />
                        <AlertDescription className="text-cream-200">
                            Your job application data will be analyzed to provide insights on skills demand,
                            application patterns, market trends, and personalized recommendations.
                        </AlertDescription>
                    </Alert>

                    <div className="flex items-center justify-center gap-3">
                        <Button
                            onClick={() => window.location.href = '/dashboard/jobs'}
                            className="bg-accent-500 hover:bg-accent-400 text-white"
                        >
                            Browse Jobs
                        </Button>
                        <Button
                            onClick={onRetry}
                            variant="outline"
                            className="border-primary-500 text-cream-300 hover:text-cream-50 hover:border-accent-500"
                        >
                            <RefreshCwIcon className="h-4 w-4 mr-2" />
                            Check Again
                        </Button>
                    </div>
                </div>
            </div>
        </div>
    )
}

function ErrorPage({ error, onRetry }: { error: string; onRetry: () => void }) {
    return (
        <div className="w-full px-6 py-6">
            <div className="flex items-center justify-center min-h-[60vh]">
                <div className="text-center space-y-6 max-w-md">
                    <div className="text-8xl">⚠️</div>
                    <div className="space-y-3">
                        <h1 className="text-2xl font-bold text-cream-50">Analytics Error</h1>
                        <p className="text-cream-300">
                            Unable to load analytics data. Please try again.
                        </p>
                    </div>

                    <Alert className="border-red-500/20 bg-red-500/10 text-left">
                        <AlertCircle className="h-4 w-4 text-red-400" />
                        <AlertDescription className="text-cream-200">
                            {error}
                        </AlertDescription>
                    </Alert>

                    <Button
                        onClick={onRetry}
                        className="bg-red-500 hover:bg-red-400 text-white"
                    >
                        <RefreshCwIcon className="h-4 w-4 mr-2" />
                        Try Again
                    </Button>
                </div>
            </div>
        </div>
    )
} 