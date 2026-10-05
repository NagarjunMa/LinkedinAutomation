"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription } from "@/components/ui/alert"
import {
    TrendingUp,
    Code2,
    Target,
    AlertCircle,
    RefreshCw,
    ExternalLink,
    Star,
    Award
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { analyticsAPI, SkillsAnalysis, isInsufficientDataError, isAnalyticsAPIError } from "@/lib/analytics-api"

interface SkillsAnalyticsCardProps {
    title?: string
    className?: string
    showActions?: boolean
}

export function SkillsAnalyticsCard({
    title = "Skills Analytics",
    className,
    showActions = true
}: SkillsAnalyticsCardProps) {
    const router = useRouter()
    const [skillsData, setSkillsData] = useState<SkillsAnalysis | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [isRefreshing, setIsRefreshing] = useState(false)

    const fetchSkillsData = async () => {
        try {
            setError(null)
            const data = await analyticsAPI.getSkillsAnalysis()
            setSkillsData(data)
        } catch (err) {
            if (isInsufficientDataError(err)) {
                setError("Insufficient data")
            } else if (isAnalyticsAPIError(err)) {
                setError(err.message)
            } else {
                setError("Failed to load skills analytics")
            }
        } finally {
            setLoading(false)
            setIsRefreshing(false)
        }
    }

    const handleRefresh = async () => {
        setIsRefreshing(true)
        await fetchSkillsData()
    }

    useEffect(() => {
        fetchSkillsData()
    }, [])

    if (loading) {
        return <SkillsAnalyticsCardSkeleton title={title} className={className} />
    }

    if (error === "Insufficient data") {
        return <InsufficientDataCard title={title} className={className} onRefresh={handleRefresh} />
    }

    if (error) {
        return <ErrorCard title={title} className={className} error={error} onRefresh={handleRefresh} />
    }

    if (!skillsData) {
        return <ErrorCard title={title} className={className} error="No data available" onRefresh={handleRefresh} />
    }

    const topSkills = (skillsData.top_skills || []).slice(0, 8)
    const trendingSkills = (skillsData.trending_skills || []).slice(0, 4)
    const recommendedSkills = (skillsData.recommended_skills || []).slice(0, 4)

    return (
        <Card className={cn(
            "premium-card hover:scale-105 transition-all duration-300 group max-h-[600px] flex flex-col",
            className
        )}>
            <CardHeader className="pb-3 shrink-0">
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                        <Code2 className="h-5 w-5 text-accent-400 group-hover:text-accent-300 transition-colors" />
                        <CardTitle className="text-cream-50 text-lg group-hover:text-accent-400 transition-colors">
                            {title}
                        </CardTitle>
                    </div>
                    {showActions && (
                        <div className="flex items-center space-x-2">
                            {skillsData.diversity_score && (
                                <Badge className="bg-gold-500/20 text-gold-400 border-gold-500/30 text-xs">
                                    Diversity: {Math.round(skillsData.diversity_score)}%
                                </Badge>
                            )}
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
                {/* Top Skills Section */}
                {topSkills.length > 0 && (
                    <div className="space-y-3">
                        <div className="flex items-center space-x-2">
                            <Star className="h-4 w-4 text-gold-400" />
                            <h4 className="text-sm font-medium text-cream-200">Top Skills in Demand</h4>
                        </div>
                        <div className="flex flex-wrap gap-2">
                            {topSkills.map((skill, index) => (
                                <div
                                    key={skill.skill}
                                    className="flex items-center space-x-2 bg-primary-700 rounded-lg px-3 py-2 hover:bg-primary-600 transition-colors group/skill"
                                >
                                    <span className={cn(
                                        "text-sm font-medium",
                                        index < 3 ? "text-gold-400" : "text-cream-200"
                                    )}>
                                        {skill.skill}
                                    </span>
                                    <Badge className={cn(
                                        "text-xs border-0",
                                        index < 3
                                            ? "bg-gold-500/20 text-gold-300"
                                            : "bg-accent-500/20 text-accent-300"
                                    )}>
                                        {skill.percentage.toFixed(0)}%
                                    </Badge>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Trending Skills Section */}
                {trendingSkills.length > 0 && (
                    <div className="space-y-3">
                        <div className="flex items-center space-x-2">
                            <TrendingUp className="h-4 w-4 text-green-400" />
                            <h4 className="text-sm font-medium text-cream-200">Trending Skills</h4>
                        </div>
                        <div className="flex flex-wrap gap-2">
                            {trendingSkills.map((skill) => (
                                <Badge
                                    key={skill}
                                    className="bg-green-500/20 text-green-300 border-green-500/30 hover:bg-green-500/30 transition-colors cursor-pointer"
                                >
                                    {skill}
                                </Badge>
                            ))}
                        </div>
                    </div>
                )}

                {/* Recommended Skills Section */}
                {recommendedSkills.length > 0 && (
                    <div className="space-y-3">
                        <div className="flex items-center space-x-2">
                            <Target className="h-4 w-4 text-accent-400" />
                            <h4 className="text-sm font-medium text-cream-200">Recommended to Learn</h4>
                        </div>
                        <div className="flex flex-wrap gap-2">
                            {recommendedSkills.map((skill) => (
                                <Badge
                                    key={skill}
                                    className="bg-accent-500/20 text-accent-300 border-accent-500/30 hover:bg-accent-500/30 transition-colors cursor-pointer"
                                >
                                    {skill}
                                </Badge>
                            ))}
                        </div>
                    </div>
                )}

                {/* Action Button */}
                {showActions && (
                    <div className="mt-auto pt-3">
                        <Button
                            className="w-full bg-primary-700 hover:bg-primary-600 text-cream-50 border-primary-500 hover:border-accent-500 transition-all duration-200 group/btn"
                            onClick={() => router.push('/dashboard/analytics')}
                        >
                            <div className="flex items-center space-x-2">
                                <Award className="h-4 w-4 group-hover/btn:text-accent-400 transition-colors" />
                                <span>View Detailed Analysis</span>
                                <ExternalLink className="h-3 w-3 group-hover/btn:text-accent-400 transition-colors" />
                            </div>
                        </Button>
                    </div>
                )}
            </CardContent>
        </Card>
    )
}

function SkillsAnalyticsCardSkeleton({ title, className }: { title: string; className?: string }) {
    return (
        <Card className={cn(
            "premium-card h-full flex flex-col",
            className
        )}>
            <CardHeader className="pb-3 shrink-0">
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                        <Code2 className="h-5 w-5 text-accent-400" />
                        <CardTitle className="text-cream-50 text-lg">{title}</CardTitle>
                    </div>
                    <Skeleton className="h-6 w-16 bg-primary-700" />
                </div>
            </CardHeader>

            <CardContent className="flex-1 flex flex-col space-y-4">
                {/* Top Skills Skeleton */}
                <div className="space-y-3">
                    <div className="flex items-center space-x-2">
                        <Star className="h-4 w-4 text-gold-400" />
                        <Skeleton className="h-4 w-32 bg-primary-700" />
                    </div>
                    <div className="flex flex-wrap gap-2">
                        {Array.from({ length: 6 }).map((_, i) => (
                            <Skeleton key={i} className="h-8 w-20 bg-primary-700" />
                        ))}
                    </div>
                </div>

                {/* Trending Skills Skeleton */}
                <div className="space-y-3">
                    <div className="flex items-center space-x-2">
                        <TrendingUp className="h-4 w-4 text-green-400" />
                        <Skeleton className="h-4 w-28 bg-primary-700" />
                    </div>
                    <div className="flex flex-wrap gap-2">
                        {Array.from({ length: 4 }).map((_, i) => (
                            <Skeleton key={i} className="h-6 w-16 bg-primary-700" />
                        ))}
                    </div>
                </div>

                {/* Recommended Skills Skeleton */}
                <div className="space-y-3">
                    <div className="flex items-center space-x-2">
                        <Target className="h-4 w-4 text-accent-400" />
                        <Skeleton className="h-4 w-36 bg-primary-700" />
                    </div>
                    <div className="flex flex-wrap gap-2">
                        {Array.from({ length: 4 }).map((_, i) => (
                            <Skeleton key={i} className="h-6 w-18 bg-primary-700" />
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
            <CardHeader className="pb-3 shrink-0">
                <div className="flex items-center space-x-2">
                    <Code2 className="h-5 w-5 text-accent-400" />
                    <CardTitle className="text-cream-50 text-lg">{title}</CardTitle>
                </div>
            </CardHeader>

            <CardContent className="flex-1 flex flex-col items-center justify-center space-y-4">
                <Alert className="border-gold-500/20 bg-gold-500/10">
                    <AlertCircle className="h-4 w-4 text-gold-400" />
                    <AlertDescription className="text-cream-200">
                        Insufficient application data for skills analysis. Apply to more jobs to unlock detailed insights.
                    </AlertDescription>
                </Alert>

                <div className="text-center space-y-2">
                    <div className="text-6xl">📊</div>
                    <p className="text-sm text-cream-300">
                        We need at least 3 job applications to generate meaningful skills analytics.
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
                    <Code2 className="h-5 w-5 text-accent-400" />
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
                        Unable to load skills analytics. Please try again.
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
