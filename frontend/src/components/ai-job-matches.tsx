"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import { useToast } from "@/components/ui/use-toast"
import {
    BrainIcon,
    TrendingUpIcon,
    MapPinIcon,
    DollarSignIcon,
    ExternalLinkIcon,
    RefreshCwIcon,
    StarIcon,
    ThumbsUpIcon,
    BuildingIcon
} from "lucide-react"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface JobMatch {
    job_id: number
    title: string
    company: string
    location: string
    salary_range: string
    application_url: string
    posted_date: string
    compatibility_score: number
    ai_reasoning: string
    match_factors: string[]
    skills_match: number
    experience_match: number
    location_match: number
}

interface AIJobMatchesProps {
    userId: string
    minScore?: number
    limit?: number
}

export function AIJobMatches({ userId, minScore = 70, limit = 10 }: AIJobMatchesProps) {
    const [jobMatches, setJobMatches] = useState<JobMatch[]>([])
    const [loading, setLoading] = useState(false)
    const [scoring, setScoring] = useState(false)
    const { toast } = useToast()

    useEffect(() => {
        fetchJobMatches()
    }, [userId, minScore, limit])

    const fetchJobMatches = async () => {
        setLoading(true)
        try {
            const response = await fetch(
                `${API_BASE_URL}/api/v1/profiles/matches/${userId}?limit=${limit}&min_score=${minScore}`
            )

            if (!response.ok) {
                if (response.status === 404) {
                    toast({
                        title: "No profile found",
                        description: "Please upload your resume first to get AI job matches",
                        variant: "destructive"
                    })
                    return
                }
                throw new Error('Failed to fetch job matches')
            }

            const data = await response.json()
            setJobMatches(data.matches || [])

        } catch (error) {
            console.error('Error fetching job matches:', error)
            toast({
                title: "Error fetching matches",
                description: "Please try again or contact support",
                variant: "destructive"
            })
        } finally {
            setLoading(false)
        }
    }

    const triggerJobScoring = async () => {
        setScoring(true)
        try {
            const response = await fetch(
                `${API_BASE_URL}/api/v1/profiles/score-jobs/${userId}?job_limit=50&days_back=7`,
                { method: 'POST' }
            )

            if (!response.ok) {
                throw new Error('Failed to score jobs')
            }

            const result = await response.json()

            toast({
                title: "AI job scoring completed!",
                description: `Analyzed ${result.jobs_scored} jobs. Found ${result.high_scores} high matches.`,
            })

            // Refresh the matches
            await fetchJobMatches()

        } catch (error) {
            console.error('Error scoring jobs:', error)
            toast({
                title: "Scoring failed",
                description: "Please try again later",
                variant: "destructive"
            })
        } finally {
            setScoring(false)
        }
    }

    const getScoreColor = (score: number) => {
        if (score >= 90) return "text-green-600"
        if (score >= 80) return "text-blue-600"
        if (score >= 70) return "text-yellow-600"
        return "text-gray-600"
    }

    const getScoreBadgeVariant = (score: number) => {
        if (score >= 90) return "default"
        if (score >= 80) return "secondary"
        return "outline"
    }

      const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString()
    } catch {
      return dateString
    }
  }

  const handleApplyToJob = async (jobId: number, applicationUrl: string) => {
    try {
      // Open the job application in new tab
      window.open(applicationUrl, '_blank')
      
      // Track the application in our system
      const formData = new FormData()
      formData.append('user_id', userId)
      formData.append('application_source', 'external')
      formData.append('notes', 'Applied via AI job matching system')
      
      const response = await fetch(`${API_BASE_URL}/api/v1/jobs/applications/${jobId}/apply`, {
        method: 'POST',
        body: formData
      })
      
      if (response.ok) {
        toast({
          title: "Application tracked!",
          description: "We've recorded your job application for tracking.",
        })
      }
    } catch (error) {
      console.error('Error tracking application:', error)
      // Don't show error to user as the main action (opening job link) still worked
    }
  }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h3 className="text-lg font-semibold">AI Job Matches</h3>
                    <p className="text-sm text-muted-foreground">
                        Jobs scored {minScore}%+ compatibility with your profile
                    </p>
                </div>
                <div className="flex gap-2">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={triggerJobScoring}
                        disabled={scoring}
                    >
                        {scoring ? (
                            <>
                                <BrainIcon className="mr-2 h-4 w-4 animate-spin" />
                                AI Analyzing...
                            </>
                        ) : (
                            <>
                                <BrainIcon className="mr-2 h-4 w-4" />
                                Score New Jobs
                            </>
                        )}
                    </Button>
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={fetchJobMatches}
                        disabled={loading}
                    >
                        <RefreshCwIcon className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                    </Button>
                </div>
            </div>

            {loading ? (
                <div className="grid gap-4">
                    {[1, 2, 3].map((i) => (
                        <Card key={i} className="animate-pulse">
                            <CardContent className="p-6">
                                <div className="space-y-3">
                                    <div className="h-4 bg-muted rounded w-3/4"></div>
                                    <div className="h-3 bg-muted rounded w-1/2"></div>
                                    <div className="h-3 bg-muted rounded w-5/6"></div>
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            ) : jobMatches.length === 0 ? (
                <Card>
                    <CardContent className="p-8 text-center">
                        <BrainIcon className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                        <h3 className="text-lg font-medium mb-2">No AI matches yet</h3>
                        <p className="text-sm text-muted-foreground mb-4">
                            Upload your resume and let our AI find the perfect job matches for you
                        </p>
                        <Button onClick={triggerJobScoring} disabled={scoring}>
                            {scoring ? (
                                <>
                                    <BrainIcon className="mr-2 h-4 w-4 animate-spin" />
                                    AI is analyzing jobs...
                                </>
                            ) : (
                                <>
                                    <BrainIcon className="mr-2 h-4 w-4" />
                                    Start AI Job Matching
                                </>
                            )}
                        </Button>
                    </CardContent>
                </Card>
            ) : (
                <div className="grid gap-4">
                    {jobMatches.map((job) => (
                        <Card key={job.job_id} className="hover:shadow-md transition-shadow">
                            <CardHeader className="pb-4">
                                <div className="flex items-start justify-between">
                                    <div className="space-y-1">
                                        <CardTitle className="text-lg">{job.title}</CardTitle>
                                        <div className="flex items-center gap-4 text-sm text-muted-foreground">
                                            <div className="flex items-center gap-1">
                                                <BuildingIcon className="h-4 w-4" />
                                                {job.company}
                                            </div>
                                            <div className="flex items-center gap-1">
                                                <MapPinIcon className="h-4 w-4" />
                                                {job.location}
                                            </div>
                                            {job.salary_range && (
                                                <div className="flex items-center gap-1">
                                                    <DollarSignIcon className="h-4 w-4" />
                                                    {job.salary_range}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                    <div className="text-right space-y-2">
                                        <Badge variant={getScoreBadgeVariant(job.compatibility_score)} className="text-lg px-3 py-1">
                                            <StarIcon className="w-3 h-3 mr-1" />
                                            {job.compatibility_score.toFixed(0)}%
                                        </Badge>
                                        <p className="text-xs text-muted-foreground">
                                            Posted: {formatDate(job.posted_date)}
                                        </p>
                                    </div>
                                </div>
                            </CardHeader>

                            <CardContent className="space-y-4">
                                {/* AI Reasoning */}
                                <div className="space-y-2">
                                    <h4 className="text-sm font-medium flex items-center gap-2">
                                        <BrainIcon className="h-4 w-4" />
                                        AI Analysis
                                    </h4>
                                    <p className="text-sm text-muted-foreground leading-relaxed">
                                        {job.ai_reasoning}
                                    </p>
                                </div>

                                {/* Match Factors */}
                                {job.match_factors && job.match_factors.length > 0 && (
                                    <div className="space-y-2">
                                        <h4 className="text-sm font-medium flex items-center gap-2">
                                            <ThumbsUpIcon className="h-4 w-4" />
                                            Matching Factors
                                        </h4>
                                        <div className="flex flex-wrap gap-1">
                                            {job.match_factors.map((factor, index) => (
                                                <Badge key={index} variant="secondary" className="text-xs">
                                                    {factor.replace('_', ' ')}
                                                </Badge>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Compatibility Breakdown */}
                                <div className="space-y-3">
                                    <h4 className="text-sm font-medium flex items-center gap-2">
                                        <TrendingUpIcon className="h-4 w-4" />
                                        Compatibility Breakdown
                                    </h4>
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                                        <div className="space-y-1">
                                            <div className="flex justify-between text-xs">
                                                <span>Skills Match</span>
                                                <span className={getScoreColor(job.skills_match)}>
                                                    {job.skills_match.toFixed(0)}%
                                                </span>
                                            </div>
                                            <Progress value={job.skills_match} className="h-2" />
                                        </div>
                                        <div className="space-y-1">
                                            <div className="flex justify-between text-xs">
                                                <span>Experience Match</span>
                                                <span className={getScoreColor(job.experience_match)}>
                                                    {job.experience_match.toFixed(0)}%
                                                </span>
                                            </div>
                                            <Progress value={job.experience_match} className="h-2" />
                                        </div>
                                        <div className="space-y-1">
                                            <div className="flex justify-between text-xs">
                                                <span>Location Match</span>
                                                <span className={getScoreColor(job.location_match)}>
                                                    {job.location_match.toFixed(0)}%
                                                </span>
                                            </div>
                                            <Progress value={job.location_match} className="h-2" />
                                        </div>
                                    </div>
                                </div>

                                <Separator />

                                {/* Actions */}
                                <div className="flex justify-between items-center">
                                    <div className="text-xs text-muted-foreground">
                                        Job ID: {job.job_id}
                                    </div>
                                                      <Button
                    variant="default"
                    size="sm"
                    onClick={() => handleApplyToJob(job.job_id, job.application_url)}
                  >
                    <ExternalLinkIcon className="mr-2 h-4 w-4" />
                    Apply Now
                  </Button>
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            )}
        </div>
    )
} 