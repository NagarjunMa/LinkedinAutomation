"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
    MapPin,
    Building2,
    Calendar,
    ExternalLink,
    Star,
    Clock,
    Briefcase,
    GraduationCap
} from "lucide-react"
import { JobSearchResult } from "@/hooks/use-job-search"
import { formatDistanceToNow } from "date-fns"

interface JobSearchResultsProps {
    results: JobSearchResult[]
    isLoading: boolean
    query: string
    onJobClick?: (job: JobSearchResult) => void
}

export function JobSearchResults({
    results,
    isLoading,
    query,
    onJobClick
}: JobSearchResultsProps) {
    const [_selectedJob, setSelectedJob] = useState<JobSearchResult | null>(null)

    const handleJobClick = (job: JobSearchResult) => {
        setSelectedJob(job)
        onJobClick?.(job)
    }

    const formatDate = (dateString: string | null) => {
        if (!dateString) return "Unknown date"
        try {
            return formatDistanceToNow(new Date(dateString), { addSuffix: true })
        } catch {
            return "Unknown date"
        }
    }

    const getCompatibilityColor = (score: number | null) => {
        if (!score) return "bg-gray-100 text-gray-800"
        if (score >= 80) return "bg-green-100 text-green-800"
        if (score >= 60) return "bg-yellow-100 text-yellow-800"
        return "bg-red-100 text-red-800"
    }

    if (isLoading) {
        return (
            <div className="space-y-4">
                {[...Array(3)].map((_, i) => (
                    <Card key={i} className="animate-pulse">
                        <CardContent className="p-4">
                            <div className="space-y-3">
                                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                                <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                                <div className="h-3 bg-gray-200 rounded w-1/4"></div>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>
        )
    }

    if (results.length === 0 && query.trim()) {
        return (
            <Card className="border-dashed">
                <CardContent className="p-8 text-center">
                    <div className="space-y-2">
                        <Building2 className="h-12 w-12 mx-auto text-gray-400" />
                        <h3 className="text-lg font-medium text-gray-900">No jobs found</h3>
                        <p className="text-gray-500">
                            No jobs found for &quot;{query}&quot;. Try searching with different keywords.
                        </p>
                    </div>
                </CardContent>
            </Card>
        )
    }

    return (
        <div className="space-y-4">
            {results.length > 0 && (
                <div className="flex items-center justify-between">
                    <p className="text-sm text-gray-600">
                        Found {results.length} job{results.length !== 1 ? 's' : ''} for &quot;{query}&quot;
                    </p>
                </div>
            )}

            {results.map((job) => (
                <Card
                    key={job.id}
                    className="hover:shadow-md transition-shadow cursor-pointer border-l-4 border-l-blue-500"
                    onClick={() => handleJobClick(job)}
                >
                    <CardHeader className="pb-3">
                        <div className="flex items-start justify-between">
                            <div className="space-y-1 flex-1">
                                <CardTitle className="text-lg font-semibold text-gray-900 line-clamp-2">
                                    {job.title}
                                </CardTitle>
                                <div className="flex items-center space-x-4 text-sm text-gray-600">
                                    <div className="flex items-center space-x-1">
                                        <Building2 className="h-4 w-4" />
                                        <span className="font-medium">{job.company}</span>
                                    </div>
                                    {job.location && (
                                        <div className="flex items-center space-x-1">
                                            <MapPin className="h-4 w-4" />
                                            <span>{job.location}</span>
                                        </div>
                                    )}
                                </div>
                            </div>

                            <div className="flex flex-col items-end space-y-2">
                                {job.compatibility_score && (
                                    <Badge className={getCompatibilityColor(job.compatibility_score)}>
                                        <Star className="h-3 w-3 mr-1" />
                                        {job.compatibility_score}% match
                                    </Badge>
                                )}
                                {job.applied && (
                                    <Badge variant="secondary" className="bg-green-100 text-green-800">
                                        Applied
                                    </Badge>
                                )}
                            </div>
                        </div>
                    </CardHeader>

                    <CardContent className="pt-0">
                        <div className="space-y-3">
                            {/* Job Details */}
                            <div className="flex flex-wrap gap-2">
                                {job.job_type && (
                                    <Badge variant="outline" className="text-xs">
                                        <Briefcase className="h-3 w-3 mr-1" />
                                        {job.job_type}
                                    </Badge>
                                )}
                                {job.experience_level && (
                                    <Badge variant="outline" className="text-xs">
                                        <GraduationCap className="h-3 w-3 mr-1" />
                                        {job.experience_level}
                                    </Badge>
                                )}
                                {job.salary_range && (
                                    <Badge variant="outline" className="text-xs">
                                        ${job.salary_range}
                                    </Badge>
                                )}
                            </div>

                            {/* Skills */}
                            {job.skills && job.skills.length > 0 && (
                                <div className="space-y-1">
                                    <p className="text-xs font-medium text-gray-700">Skills:</p>
                                    <div className="flex flex-wrap gap-1">
                                        {job.skills.slice(0, 5).map((skill, index) => (
                                            <Badge key={index} variant="secondary" className="text-xs">
                                                {skill}
                                            </Badge>
                                        ))}
                                        {job.skills.length > 5 && (
                                            <Badge variant="secondary" className="text-xs">
                                                +{job.skills.length - 5} more
                                            </Badge>
                                        )}
                                    </div>
                                </div>
                            )}

                            {/* Description Preview */}
                            {job.description && (
                                <p className="text-sm text-gray-600 line-clamp-2">
                                    {job.description}
                                </p>
                            )}

                            {/* Footer */}
                            <div className="flex items-center justify-between pt-2 border-t">
                                <div className="flex items-center space-x-4 text-xs text-gray-500">
                                    <div className="flex items-center space-x-1">
                                        <Clock className="h-3 w-3" />
                                        <span>Posted {formatDate(job.posted_date)}</span>
                                    </div>
                                    <div className="flex items-center space-x-1">
                                        <Calendar className="h-3 w-3" />
                                        <span>Added {formatDate(job.extracted_date)}</span>
                                    </div>
                                </div>

                                <div className="flex items-center space-x-2">
                                    {job.source && (
                                        <Badge variant="outline" className="text-xs">
                                            {job.source}
                                        </Badge>
                                    )}
                                    {job.application_url && (
                                        <Button
                                            size="sm"
                                            variant="outline"
                                            onClick={(e) => {
                                                e.stopPropagation()
                                                window.open(job.application_url!, '_blank')
                                            }}
                                        >
                                            <ExternalLink className="h-3 w-3 mr-1" />
                                            Apply
                                        </Button>
                                    )}
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            ))}
        </div>
    )
}
