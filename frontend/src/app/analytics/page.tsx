"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useToast } from "@/components/ui/use-toast"
import { Progress } from "@/components/ui/progress"
import { Skeleton } from "@/components/ui/skeleton"
import {
    ArrowLeftIcon,
    RefreshCwIcon,
    TrendingUpIcon,
    BarChart3Icon,
    MapPinIcon,
    BrainIcon,
    SearchIcon,
    TargetIcon,
    GraduationCapIcon,
    DollarSignIcon,
    UsersIcon,
    ClockIcon
} from "lucide-react"
import { useRouter } from "next/navigation"

// Utility function to safely render values that might be objects
const safeRender = (value: any): string => {
    if (value === null || value === undefined) return 'N/A'
    if (typeof value === 'string' || typeof value === 'number') return String(value)
    if (typeof value === 'object') {
        // Handle salary range objects
        if (value.min !== undefined && value.max !== undefined) {
            return `$${value.min}k - $${value.max}k`
        }
        // Handle other objects by stringifying
        return JSON.stringify(value)
    }
    return String(value)
}

interface AnalyticsData {
    executive: any
    market: any
    skills: any
    recommendations: any
    job_matches: any
    search_queries: any
    last_updated: string
}

export default function AnalyticsPage() {
    const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null)
    const [loading, setLoading] = useState(true)
    const [userSkills, setUserSkills] = useState("")
    const [experienceLevel, setExperienceLevel] = useState("mid")
    const { toast } = useToast()
    const router = useRouter()

    const fetchAnalytics = async () => {
        try {
            setLoading(true)
            const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

            const queryParams = new URLSearchParams({
                experience_level: experienceLevel,
                ...(userSkills && { skills: userSkills })
            })

            const response = await fetch(`${API_URL}/api/v1/analytics/dashboard-all?${queryParams}`)

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`)
            }

            const data = await response.json()
            setAnalyticsData(data)

        } catch (error) {
            console.error('Failed to fetch analytics:', error)
            toast({
                title: "Error",
                description: "Failed to load analytics data. Please try again.",
                variant: "destructive",
            })
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchAnalytics()
    }, [])

    if (loading) {
        return (
            <div className="container mx-auto px-4 py-8">
                <div className="space-y-6">
                    <Skeleton className="h-8 w-80" />
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        {[...Array(4)].map((_, i) => (
                            <Skeleton key={i} className="h-32" />
                        ))}
                    </div>
                    <Skeleton className="h-96 w-full" />
                </div>
            </div>
        )
    }

    const executive = analyticsData?.executive
    const market = analyticsData?.market
    const skills = analyticsData?.skills
    const recommendations = analyticsData?.recommendations
    const jobMatches = analyticsData?.job_matches
    const searchQueries = analyticsData?.search_queries

    return (
        <div className="container mx-auto px-4 py-8">
            <div className="space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Button
                            onClick={() => router.push('/dashboard')}
                            variant="outline"
                            size="sm"
                        >
                            <ArrowLeftIcon className="h-4 w-4" />
                            Back to Dashboard
                        </Button>
                        <div>
                            <h1 className="text-3xl font-bold tracking-tight">Job Search Analytics</h1>
                            <p className="text-muted-foreground">
                                AI-powered insights to optimize your job search strategy
                            </p>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        <Select value={experienceLevel} onValueChange={setExperienceLevel}>
                            <SelectTrigger className="w-32">
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="junior">Junior</SelectItem>
                                <SelectItem value="mid">Mid</SelectItem>
                                <SelectItem value="senior">Senior</SelectItem>
                            </SelectContent>
                        </Select>
                        <Button onClick={fetchAnalytics} variant="outline" size="sm">
                            <RefreshCwIcon className="h-4 w-4 mr-2" />
                            Refresh
                        </Button>
                    </div>
                </div>

                {/* User Skills Input */}
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center gap-4">
                            <div className="flex-1">
                                <Input
                                    placeholder="Enter your skills (comma-separated) to get personalized insights..."
                                    value={userSkills}
                                    onChange={(e) => setUserSkills(e.target.value)}
                                />
                            </div>
                            <Button onClick={fetchAnalytics}>
                                Update Analysis
                            </Button>
                        </div>
                    </CardContent>
                </Card>

                {/* Executive Dashboard - Key Metrics */}
                {executive && (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        <Card>
                            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                <CardTitle className="text-sm font-medium">Total Jobs</CardTitle>
                                <BarChart3Icon className="h-4 w-4 text-muted-foreground" />
                            </CardHeader>
                            <CardContent>
                                <div className="text-2xl font-bold">{executive.total_jobs}</div>
                                <p className="text-xs text-muted-foreground">
                                    {executive.new_jobs_7d} new in last 7 days
                                </p>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                <CardTitle className="text-sm font-medium">Applications</CardTitle>
                                <TargetIcon className="h-4 w-4 text-muted-foreground" />
                            </CardHeader>
                            <CardContent>
                                <div className="text-2xl font-bold">{executive.total_applications}</div>
                                <p className="text-xs text-muted-foreground">
                                    {typeof executive.conversion_rate === 'number' ? executive.conversion_rate : 0}% conversion rate
                                </p>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                <CardTitle className="text-sm font-medium">Avg Salary</CardTitle>
                                <DollarSignIcon className="h-4 w-4 text-muted-foreground" />
                            </CardHeader>
                            <CardContent>
                                <div className="text-2xl font-bold">
                                    {safeRender(executive.avg_salary_range)}
                                </div>
                                <p className="text-xs text-muted-foreground">
                                    Market average range
                                </p>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                <CardTitle className="text-sm font-medium">Top Location</CardTitle>
                                <MapPinIcon className="h-4 w-4 text-muted-foreground" />
                            </CardHeader>
                            <CardContent>
                                <div className="text-lg font-bold">{executive.top_location}</div>
                                <p className="text-xs text-muted-foreground">
                                    {executive.location_job_count} jobs available
                                </p>
                            </CardContent>
                        </Card>
                    </div>
                )}

                {/* Analytics Tabs */}
                <Tabs defaultValue="overview" className="space-y-4">
                    <TabsList className="grid w-full grid-cols-6">
                        <TabsTrigger value="overview">Overview</TabsTrigger>
                        <TabsTrigger value="market">Market</TabsTrigger>
                        <TabsTrigger value="skills">Skills</TabsTrigger>
                        <TabsTrigger value="search">Search</TabsTrigger>
                        <TabsTrigger value="predictions">Predictions</TabsTrigger>
                        <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
                    </TabsList>

                    {/* Overview Tab */}
                    <TabsContent value="overview" className="space-y-4">
                        {executive && (
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                                <Card>
                                    <CardHeader>
                                        <CardTitle className="flex items-center gap-2">
                                            <TrendingUpIcon className="h-5 w-5" />
                                            Application Performance
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="space-y-4">
                                            <div>
                                                <div className="flex justify-between text-sm">
                                                    <span>Conversion Rate</span>
                                                    <span>{typeof executive.conversion_rate === 'number' ? executive.conversion_rate : 0}%</span>
                                                </div>
                                                <Progress value={typeof executive.conversion_rate === 'number' ? executive.conversion_rate : 0} className="mt-1" />
                                            </div>
                                            <div>
                                                <div className="flex justify-between text-sm">
                                                    <span>Weekly Growth</span>
                                                    <span>{typeof executive.weekly_growth === 'number' ? executive.weekly_growth : 0}%</span>
                                                </div>
                                                <Progress value={typeof executive.weekly_growth === 'number' ? Math.abs(executive.weekly_growth) : 0} className="mt-1" />
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>

                                <Card>
                                    <CardHeader>
                                        <CardTitle className="flex items-center gap-2">
                                            <ClockIcon className="h-5 w-5" />
                                            Activity Timeline
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="space-y-2 text-sm">
                                            <div className="flex justify-between">
                                                <span>Peak Activity Day</span>
                                                <span className="font-medium">{executive.peak_day}</span>
                                            </div>
                                            <div className="flex justify-between">
                                                <span>Best Application Time</span>
                                                <span className="font-medium">{executive.best_time}</span>
                                            </div>
                                            <div className="flex justify-between">
                                                <span>Last Updated</span>
                                                <span className="font-medium">
                                                    {analyticsData?.last_updated ? new Date(analyticsData.last_updated).toLocaleDateString() : 'N/A'}
                                                </span>
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>
                            </div>
                        )}
                    </TabsContent>

                    {/* Market Intelligence Tab */}
                    <TabsContent value="market" className="space-y-4">
                        {market && (
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                                <Card>
                                    <CardHeader>
                                        <CardTitle className="flex items-center gap-2">
                                            <TrendingUpIcon className="h-5 w-5" />
                                            Tech Stack Trends
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="space-y-3">
                                            {market.tech_stack_trends?.slice(0, 5).map((tech: any, index: number) => (
                                                <div key={index} className="flex items-center justify-between">
                                                    <span className="font-medium">{tech.technology}</span>
                                                    <div className="flex items-center gap-2">
                                                        <Badge variant="outline">{tech.job_count} jobs</Badge>
                                                        <Badge variant={tech.growth > 0 ? "default" : "secondary"}>
                                                            {tech.growth > 0 ? '+' : ''}{tech.growth}%
                                                        </Badge>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </CardContent>
                                </Card>

                                <Card>
                                    <CardHeader>
                                        <CardTitle className="flex items-center gap-2">
                                            <MapPinIcon className="h-5 w-5" />
                                            Location Analysis
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="space-y-3">
                                            {market.location_analysis?.slice(0, 5).map((location: any, index: number) => (
                                                <div key={index} className="flex items-center justify-between">
                                                    <span className="font-medium">{location.location}</span>
                                                    <div className="flex items-center gap-2">
                                                        <Badge variant="outline">{location.job_count} jobs</Badge>
                                                        <Badge variant="secondary">
                                                            {safeRender(location.avg_salary)}
                                                        </Badge>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </CardContent>
                                </Card>

                                <Card>
                                    <CardHeader>
                                        <CardTitle className="flex items-center gap-2">
                                            <UsersIcon className="h-5 w-5" />
                                            Industry Trends
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="space-y-3">
                                            {market.industry_trends?.slice(0, 5).map((company: any, index: number) => (
                                                <div key={index} className="flex items-center justify-between">
                                                    <span className="font-medium">{company.company}</span>
                                                    <div className="flex items-center gap-2">
                                                        <Badge variant="outline">{company.job_count} jobs</Badge>
                                                        <Badge variant="secondary">{company.hiring_rate}% active</Badge>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </CardContent>
                                </Card>

                                <Card>
                                    <CardHeader>
                                        <CardTitle>Market Summary</CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="space-y-2 text-sm">
                                            <div>
                                                <span className="font-medium">Hottest Skills: </span>
                                                {Array.isArray(market.market_summary?.hottest_skills)
                                                    ? market.market_summary.hottest_skills.join(", ")
                                                    : market.market_summary?.hottest_skills || "N/A"
                                                }
                                            </div>
                                            <div>
                                                <span className="font-medium">Growing Locations: </span>
                                                {Array.isArray(market.market_summary?.growing_locations)
                                                    ? market.market_summary.growing_locations.join(", ")
                                                    : market.market_summary?.growing_locations || "N/A"
                                                }
                                            </div>
                                            <div>
                                                <span className="font-medium">Best Timing: </span>
                                                {typeof market.timing_insights?.best_time === 'object'
                                                    ? JSON.stringify(market.timing_insights.best_time)
                                                    : market.timing_insights?.best_time || "N/A"
                                                }
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>
                            </div>
                        )}
                    </TabsContent>

                    {/* Skills Analysis Tab */}
                    <TabsContent value="skills" className="space-y-4">
                        {skills && (
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                                <Card>
                                    <CardHeader>
                                        <CardTitle className="flex items-center gap-2">
                                            <BrainIcon className="h-5 w-5" />
                                            Skills Demand Analysis
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="space-y-3">
                                            {skills.skills_demand?.slice(0, 8).map((skill: any, index: number) => (
                                                <div key={index} className="flex items-center justify-between">
                                                    <span className="font-medium">{skill.skill}</span>
                                                    <div className="flex items-center gap-2">
                                                        <Badge variant="outline">{skill.job_count} jobs</Badge>
                                                        <Badge variant={skill.market_score > 70 ? "default" : "secondary"}>
                                                            {skill.market_score} score
                                                        </Badge>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </CardContent>
                                </Card>

                                <Card>
                                    <CardHeader>
                                        <CardTitle>Skills Gap Analysis</CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        {userSkills ? (
                                            <div className="space-y-3">
                                                <div>
                                                    <span className="font-medium text-green-600">Your Skills: </span>
                                                    <div className="flex flex-wrap gap-1 mt-1">
                                                        {userSkills.split(',').map((skill, index) => (
                                                            <Badge key={index} variant="secondary">{skill.trim()}</Badge>
                                                        ))}
                                                    </div>
                                                </div>
                                                {skills.missing_skills && (
                                                    <div>
                                                        <span className="font-medium text-orange-600">Missing Skills: </span>
                                                        <div className="flex flex-wrap gap-1 mt-1">
                                                            {skills.missing_skills.slice(0, 6).map((skill: string, index: number) => (
                                                                <Badge key={index} variant="outline">{skill}</Badge>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        ) : (
                                            <p className="text-muted-foreground text-sm">
                                                Enter your skills above to see gap analysis
                                            </p>
                                        )}
                                    </CardContent>
                                </Card>
                            </div>
                        )}
                    </TabsContent>

                    {/* Search Performance Tab */}
                    <TabsContent value="search" className="space-y-4">
                        {searchQueries && (
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                                <Card>
                                    <CardHeader>
                                        <CardTitle className="flex items-center gap-2">
                                            <SearchIcon className="h-5 w-5" />
                                            Search Performance
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="space-y-4">
                                            <div>
                                                <div className="flex justify-between text-sm">
                                                    <span>Avg Conversion Rate</span>
                                                    <span>{searchQueries.summary?.avg_conversion_rate || 0}%</span>
                                                </div>
                                                <Progress value={searchQueries.summary?.avg_conversion_rate || 0} className="mt-1" />
                                            </div>
                                            <div className="space-y-2 text-sm">
                                                <div className="flex justify-between">
                                                    <span>Total Queries</span>
                                                    <span className="font-medium">{searchQueries.summary?.total_queries || 0}</span>
                                                </div>
                                                <div className="flex justify-between">
                                                    <span>Active Queries</span>
                                                    <span className="font-medium">{searchQueries.summary?.active_queries || 0}</span>
                                                </div>
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>

                                <Card>
                                    <CardHeader>
                                        <CardTitle>Top Performing Queries</CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="space-y-3">
                                            {searchQueries.top_queries?.slice(0, 5).map((query: any, index: number) => (
                                                <div key={index} className="flex items-center justify-between">
                                                    <div className="flex-1 min-w-0">
                                                        <p className="font-medium truncate">{query.keywords}</p>
                                                        <p className="text-xs text-muted-foreground">{query.location}</p>
                                                    </div>
                                                    <div className="flex items-center gap-2">
                                                        <Badge variant="outline">{query.results_count} results</Badge>
                                                        <Badge variant="secondary">{query.conversion_rate}%</Badge>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </CardContent>
                                </Card>
                            </div>
                        )}
                    </TabsContent>

                    {/* Job Predictions Tab */}
                    <TabsContent value="predictions" className="space-y-4">
                        {jobMatches && (
                            <div className="space-y-4">
                                <Card>
                                    <CardHeader>
                                        <CardTitle className="flex items-center gap-2">
                                            <TargetIcon className="h-5 w-5" />
                                            AI Job Match Predictions
                                        </CardTitle>
                                        <CardDescription>
                                            Jobs ranked by AI-calculated match score based on your profile
                                        </CardDescription>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="space-y-4">
                                            {jobMatches.job_matches?.slice(0, 6).map((job: any, index: number) => (
                                                <div key={index} className="border rounded-lg p-4">
                                                    <div className="flex items-start justify-between">
                                                        <div className="flex-1">
                                                            <h4 className="font-medium">{job.title}</h4>
                                                            <p className="text-sm text-muted-foreground">{job.company} • {job.location}</p>
                                                            <div className="flex items-center gap-2 mt-2">
                                                                <Badge variant="outline">{job.job_type}</Badge>
                                                                <Badge variant="secondary">{job.experience_level}</Badge>
                                                            </div>
                                                        </div>
                                                        <div className="text-right">
                                                            <div className="text-lg font-bold text-green-600">{job.match_score}%</div>
                                                            <p className="text-xs text-muted-foreground">match score</p>
                                                        </div>
                                                    </div>
                                                    {job.match_reasons && Array.isArray(job.match_reasons) && (
                                                        <div className="mt-3">
                                                            <p className="text-xs font-medium text-muted-foreground mb-1">Match Reasons:</p>
                                                            <div className="flex flex-wrap gap-1">
                                                                {job.match_reasons.slice(0, 3).map((reason: string, i: number) => (
                                                                    <Badge key={i} variant="outline" className="text-xs">
                                                                        {typeof reason === 'string' ? reason : String(reason)}
                                                                    </Badge>
                                                                ))}
                                                            </div>
                                                        </div>
                                                    )}
                                                </div>
                                            ))}
                                        </div>
                                    </CardContent>
                                </Card>
                            </div>
                        )}
                    </TabsContent>

                    {/* Recommendations Tab */}
                    <TabsContent value="recommendations" className="space-y-4">
                        <Card>
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <GraduationCapIcon className="h-5 w-5" />
                                    Learning Recommendations
                                </CardTitle>
                                <CardDescription>
                                    Based on analysis of your job listings
                                </CardDescription>
                            </CardHeader>
                            <CardContent>
                                {recommendations ? (
                                    <div className="space-y-4">
                                        {/* Skills to Learn */}
                                        {recommendations.skills_to_learn && (
                                            <div className="space-y-2">
                                                <h3 className="font-medium">Skills to Learn</h3>
                                                {recommendations.skills_to_learn.map((skill: any, index: number) => (
                                                    <div key={index} className="border rounded-lg p-3">
                                                        <div className="flex items-center justify-between">
                                                            <div>
                                                                <h4 className="font-medium">{skill.skill}</h4>
                                                                <p className="text-sm text-muted-foreground">{skill.category}</p>
                                                            </div>
                                                            <div className="flex gap-2">
                                                                <Badge variant="outline">{skill.demand} jobs</Badge>
                                                                <Badge variant={skill.priority === 'High' ? 'default' : 'secondary'}>
                                                                    {skill.priority}
                                                                </Badge>
                                                            </div>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        )}

                                        {/* Certifications */}
                                        {recommendations.certifications && (
                                            <div className="space-y-2">
                                                <h3 className="font-medium">Recommended Certifications</h3>
                                                {recommendations.certifications.map((cert: any, index: number) => (
                                                    <div key={index} className="border rounded-lg p-3">
                                                        <div className="flex items-center justify-between">
                                                            <h4 className="font-medium text-sm">{cert.name}</h4>
                                                            <div className="flex gap-2">
                                                                <Badge variant={cert.priority === 'High' ? 'default' : 'secondary'}>
                                                                    {cert.priority}
                                                                </Badge>
                                                                <Badge variant="outline">{cert.duration}</Badge>
                                                            </div>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        )}

                                        {/* Resume Tips */}
                                        {recommendations.resume_optimization && (
                                            <div className="space-y-2">
                                                <h3 className="font-medium">Resume Optimization Tips</h3>
                                                {recommendations.resume_optimization.map((tip: any, index: number) => (
                                                    <div key={index} className="border-l-4 border-blue-500 pl-4 py-2">
                                                        <h4 className="font-medium text-sm">{tip.category}</h4>
                                                        <p className="text-sm text-muted-foreground">{tip.tip}</p>
                                                        <p className="text-xs text-blue-600 mt-1">{tip.action}</p>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                ) : (
                                    <div className="flex items-center gap-2">
                                        <RefreshCwIcon className="h-4 w-4 animate-spin" />
                                        <span className="text-sm text-muted-foreground">
                                            Loading recommendations...
                                        </span>
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </TabsContent>
                </Tabs>
            </div>
        </div>
    )
} 