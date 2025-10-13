"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription } from "@/components/ui/alert"
import {
    MapPin,
    Building,
    DollarSign,
    Briefcase,
    TrendingUp,
    AlertCircle,
    RefreshCw,
    ExternalLink,
    Target,
    Settings
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useState, useEffect } from "react"
import { analyticsAPI, PreferencesAnalysis, isInsufficientDataError, isAnalyticsAPIError } from "@/lib/analytics-api"

interface PreferencesAnalyticsCardProps {
    title?: string
    className?: string
    showActions?: boolean
}

export function PreferencesAnalyticsCard({
    title = "Job Preferences",
    className,
    showActions = true
}: PreferencesAnalyticsCardProps) {
    const [preferencesData, setPreferencesData] = useState<PreferencesAnalysis | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [isRefreshing, setIsRefreshing] = useState(false)

    const fetchPreferencesData = async () => {
        try {
            setError(null)
            const fullData = await analyticsAPI.getFullAnalytics(30)
            setPreferencesData(fullData.preferences)
        } catch (err) {
            if (isInsufficientDataError(err)) {
                setError("Insufficient data")
            } else if (isAnalyticsAPIError(err)) {
                setError(err.message)
            } else {
                setError("Failed to load preferences analytics")
            }
        } finally {
            setLoading(false)
            setIsRefreshing(false)
        }
    }

    const handleRefresh = async () => {
        setIsRefreshing(true)
        await fetchPreferencesData()
    }

    useEffect(() => {
        fetchPreferencesData()
    }, [])

    if (loading) {
        return <PreferencesAnalyticsCardSkeleton title={title} className={className} />
    }

    if (error === "Insufficient data") {
        return <InsufficientDataCard title={title} className={className} onRefresh={handleRefresh} />
    }

    if (error) {
        return <ErrorCard title={title} className={className} error={error} onRefresh={handleRefresh} />
    }

    if (!preferencesData) {
        return <ErrorCard title={title} className={className} error="No data available" onRefresh={handleRefresh} />
    }

    // Process work location data
    const workLocationEntries = Object.entries(preferencesData.work_location || {})
        .sort(([, a], [, b]) => b.percentage - a.percentage)
        .slice(0, 3)

    // Process company sizes data
    const companySizeEntries = Object.entries(preferencesData.company_sizes || {})
        .sort(([, a], [, b]) => b.percentage - a.percentage)
        .slice(0, 3)

    // Process job titles
    const topJobTitles = (preferencesData.job_titles?.distribution || [])
        .sort((a, b) => b.percentage - a.percentage)
        .slice(0, 4)

    return (
        <Card className={cn(
            "premium-card hover:scale-105 transition-all duration-300 group max-h-[600px] flex flex-col",
            className
        )}>
            <CardHeader className="pb-3 flex-shrink-0">
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                        <Settings className="h-5 w-5 text-accent-400 group-hover:text-accent-300 transition-colors" />
                        <CardTitle className="text-cream-50 text-lg group-hover:text-accent-400 transition-colors">
                            {title}
                        </CardTitle>
                    </div>
                    {showActions && (
                        <div className="flex items-center space-x-2">
                            <Badge className="bg-accent-500/20 text-accent-400 border-accent-500/30 text-xs">
                                {preferencesData.job_titles.diversity_score} job types
                            </Badge>
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
            </CardHeader>

            <CardContent className="flex-1 flex flex-col space-y-4 min-h-0 overflow-y-auto">
                {/* Primary Job Focus */}
                {preferencesData.job_titles.primary_focus && (
                    <div className="bg-primary-700 rounded-lg p-3 border border-accent-500/20">
                        <div className="flex items-center space-x-2 mb-2">
                            <Target className="h-4 w-4 text-accent-400" />
                            <span className="text-sm font-medium text-cream-200">Primary Focus</span>
                        </div>
                        <div className="text-lg font-semibold text-accent-400">
                            {preferencesData.job_titles.primary_focus}
                        </div>
                    </div>
                )}

                {/* Work Location Preferences */}
                {workLocationEntries.length > 0 && (
                    <div className="space-y-3">
                        <div className="flex items-center space-x-2">
                            <MapPin className="h-4 w-4 text-blue-400" />
                            <h4 className="text-sm font-medium text-cream-200">Work Location</h4>
                        </div>
                        <div className="space-y-2">
                            {workLocationEntries.map(([location, data]) => (
                                <div key={location} className="flex items-center justify-between">
                                    <span className="text-sm text-cream-300 capitalize">{location}</span>
                                    <div className="flex items-center space-x-2">
                                        <Progress
                                            value={data.percentage}
                                            className="w-16 h-2"
                                        />
                                        <span className="text-xs text-cream-400 w-8">
                                            {Math.round(data.percentage)}%
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Job Titles */}
                {topJobTitles.length > 0 && (
                    <div className="space-y-3">
                        <div className="flex items-center space-x-2">
                            <Briefcase className="h-4 w-4 text-gold-400" />
                            <h4 className="text-sm font-medium text-cream-200">Job Types</h4>
                        </div>
                        <div className="flex flex-wrap gap-2">
                            {topJobTitles.map((job, index) => (
                                <div
                                    key={job.title}
                                    className="flex items-center space-x-2 bg-primary-700 rounded-lg px-3 py-2 hover:bg-primary-600 transition-colors"
                                >
                                    <span className={cn(
                                        "text-sm font-medium",
                                        index === 0 ? "text-gold-400" : "text-cream-200"
                                    )}>
                                        {job.title.length > 20 ? `${job.title.slice(0, 20)}...` : job.title}
                                    </span>
                                    <Badge className={cn(
                                        "text-xs border-0",
                                        index === 0
                                            ? "bg-gold-500/20 text-gold-300"
                                            : "bg-accent-500/20 text-accent-300"
                                    )}>
                                        {Math.round(job.percentage)}%
                                    </Badge>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Company Sizes */}
                {companySizeEntries.length > 0 && (
                    <div className="space-y-3">
                        <div className="flex items-center space-x-2">
                            <Building className="h-4 w-4 text-purple-400" />
                            <h4 className="text-sm font-medium text-cream-200">Company Size</h4>
                        </div>
                        <div className="grid grid-cols-3 gap-2">
                            {companySizeEntries.map(([size, data]) => (
                                <div key={size} className="text-center bg-primary-700 rounded-lg p-2">
                                    <div className="text-xs text-cream-300 capitalize mb-1">
                                        {size === "startup" ? "Startup" :
                                         size === "small" ? "Small" :
                                         size === "medium" ? "Medium" :
                                         size === "large" ? "Large" :
                                         size === "enterprise" ? "Enterprise" : size}
                                    </div>
                                    <div className="text-sm font-semibold text-purple-400">
                                        {Math.round(data.percentage)}%
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Salary Information */}
                {preferencesData.salary_ranges && preferencesData.salary_ranges.count > 0 && (
                    <div className="space-y-3">
                        <div className="flex items-center space-x-2">
                            <DollarSign className="h-4 w-4 text-green-400" />
                            <h4 className="text-sm font-medium text-cream-200">Salary Insights</h4>
                        </div>
                        <div className="bg-primary-700 rounded-lg p-3">
                            <div className="grid grid-cols-2 gap-3 text-center">
                                {preferencesData.salary_ranges.average && (
                                    <div>
                                        <div className="text-xs text-cream-300">Average</div>
                                        <div className="text-sm font-semibold text-green-400">
                                            ${preferencesData.salary_ranges.average.toLocaleString()}
                                        </div>
                                    </div>
                                )}
                                <div>
                                    <div className="text-xs text-cream-300">Jobs w/ Salary</div>
                                    <div className="text-sm font-semibold text-green-400">
                                        {preferencesData.salary_ranges.count}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Action Button */}
                {showActions && (
                    <div className="mt-auto pt-3">
                        <Button
                            className="w-full bg-primary-700 hover:bg-primary-600 text-cream-50 border-primary-500 hover:border-accent-500 transition-all duration-200 group/btn"
                            onClick={() => {
                                window.location.href = '/dashboard/analytics'
                            }}
                        >
                            <div className="flex items-center space-x-2">
                                <TrendingUp className="h-4 w-4 group-hover/btn:text-accent-400 transition-colors" />
                                <span>View Detailed Preferences</span>
                                <ExternalLink className="h-3 w-3 group-hover/btn:text-accent-400 transition-colors" />
                            </div>
                        </Button>
                    </div>
                )}
            </CardContent>
        </Card>
    )
}

function PreferencesAnalyticsCardSkeleton({ title, className }: { title: string; className?: string }) {
    return (
        <Card className={cn(
            "premium-card h-full flex flex-col",
            className
        )}>
            <CardHeader className="pb-3 flex-shrink-0">
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                        <Settings className="h-5 w-5 text-accent-400" />
                        <CardTitle className="text-cream-50 text-lg">{title}</CardTitle>
                    </div>
                    <Skeleton className="h-6 w-16 bg-primary-700" />
                </div>
            </CardHeader>

            <CardContent className="flex-1 flex flex-col space-y-4">
                {/* Primary Focus Skeleton */}
                <Skeleton className="h-16 w-full bg-primary-700" />

                {/* Work Location Skeleton */}
                <div className="space-y-3">
                    <div className="flex items-center space-x-2">
                        <MapPin className="h-4 w-4 text-blue-400" />
                        <Skeleton className="h-4 w-24 bg-primary-700" />
                    </div>
                    <div className="space-y-2">
                        {Array.from({ length: 3 }).map((_, i) => (
                            <div key={i} className="flex items-center justify-between">
                                <Skeleton className="h-4 w-16 bg-primary-700" />
                                <Skeleton className="h-2 w-20 bg-primary-700" />
                            </div>
                        ))}
                    </div>
                </div>

                {/* Job Types Skeleton */}
                <div className="space-y-3">
                    <div className="flex items-center space-x-2">
                        <Briefcase className="h-4 w-4 text-gold-400" />
                        <Skeleton className="h-4 w-20 bg-primary-700" />
                    </div>
                    <div className="flex flex-wrap gap-2">
                        {Array.from({ length: 4 }).map((_, i) => (
                            <Skeleton key={i} className="h-8 w-24 bg-primary-700" />
                        ))}
                    </div>
                </div>

                <Skeleton className="h-10 w-full bg-primary-700 mt-auto" />
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
            <CardHeader className="pb-3 flex-shrink-0">
                <div className="flex items-center space-x-2">
                    <Settings className="h-5 w-5 text-accent-400" />
                    <CardTitle className="text-cream-50 text-lg">{title}</CardTitle>
                </div>
            </CardHeader>

            <CardContent className="flex-1 flex flex-col items-center justify-center space-y-4">
                <Alert className="border-gold-500/20 bg-gold-500/10">
                    <AlertCircle className="h-4 w-4 text-gold-400" />
                    <AlertDescription className="text-cream-200">
                        Insufficient application data for preferences analysis. Apply to more jobs to understand your patterns.
                    </AlertDescription>
                </Alert>

                <div className="text-center space-y-2">
                    <div className="text-6xl">⚙️</div>
                    <p className="text-sm text-cream-300">
                        We analyze your job preferences based on your application history.
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
            <CardHeader className="pb-3 flex-shrink-0">
                <div className="flex items-center space-x-2">
                    <Settings className="h-5 w-5 text-accent-400" />
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
                        Unable to load preferences analytics. Please try again.
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