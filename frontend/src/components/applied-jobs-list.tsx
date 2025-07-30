"use client"

import { useEffect, useState, useRef } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ExternalLink, Building, Calendar, Zap, Brain } from "lucide-react"
import { format, isValid, parseISO } from "date-fns"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface JobApplication {
    id: number
    user_id: string
    job_id: number
    application_status: string
    application_source: string
    application_date: string
    source_url?: string
    user_notes?: string
    extraction_metadata?: {
        extraction_confidence?: number
        extraction_method?: string
    }
    job_listing: {
        id: number
        title: string
        company: string
        location?: string
        description?: string
        job_type?: string
        experience_level?: string
        salary_range?: string
        skills?: string[]
        application_url?: string
        source: string
        posted_date?: string
    }
}

interface AppliedJobsListProps {
    userId: string
    limit?: number
}

function formatDate(dateString: string): string {
    try {
        const date = parseISO(dateString)
        if (!isValid(date)) {
            return 'Invalid date'
        }
        return format(date, 'MMM d, yyyy')
    } catch (error) {
        return 'Invalid date'
    }
}

function getStatusColor(status: string): string {
    switch (status.toLowerCase()) {
        case 'interested': return 'bg-blue-100 text-blue-800 border-blue-200'
        case 'applied': return 'bg-green-100 text-green-800 border-green-200'
        case 'interviewing': return 'bg-yellow-100 text-yellow-800 border-yellow-200'
        case 'rejected': return 'bg-red-100 text-red-800 border-red-200'
        case 'offer': return 'bg-purple-100 text-purple-800 border-purple-200'
        default: return 'bg-gray-100 text-gray-800 border-gray-200'
    }
}

// Custom hook for tilt effect
function useTiltEffect() {
    const ref = useRef<HTMLDivElement>(null)

    useEffect(() => {
        const element = ref.current
        if (!element) return

        const handleMouseMove = (e: MouseEvent) => {
            const rect = element.getBoundingClientRect()
            const x = e.clientX - rect.left
            const y = e.clientY - rect.top
            const centerX = rect.width / 2
            const centerY = rect.height / 2
            const rotateX = (y - centerY) / 10
            const rotateY = (centerX - x) / 10

            element.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.02, 1.02, 1.02)`
        }

        const handleMouseLeave = () => {
            element.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)'
        }

        element.addEventListener('mousemove', handleMouseMove)
        element.addEventListener('mouseleave', handleMouseLeave)

        return () => {
            element.removeEventListener('mousemove', handleMouseMove)
            element.removeEventListener('mouseleave', handleMouseLeave)
        }
    }, [])

    return ref
}

// Individual job card component
function JobApplicationCard({ application }: { application: JobApplication }) {
    const tiltRef = useTiltEffect()
    const aiScore = application.extraction_metadata?.extraction_confidence
        ? Math.round(application.extraction_metadata.extraction_confidence * 100)
        : null

    return (
        <div
            ref={tiltRef}
            className="transition-transform duration-300 ease-out"
            style={{ transformStyle: 'preserve-3d' }}
        >
            <Card className="h-full border border-gray-200 shadow-sm hover:shadow-xl transition-all duration-300 bg-white">
                <CardContent className="p-6">
                    <div className="space-y-4">
                        {/* Header with Role and Company */}
                        <div className="space-y-2">
                            <h3 className="font-bold text-xl leading-tight text-gray-800 hover:text-blue-700 transition-colors">
                                {application.job_listing.title}
                            </h3>
                            <div className="flex items-center gap-2 text-gray-600">
                                <Building className="h-4 w-4" />
                                <span className="font-medium">{application.job_listing.company}</span>
                            </div>
                        </div>

                        {/* Salary and Location */}
                        <div className="flex items-center justify-between">
                            <div className="space-y-1">
                                {application.job_listing.salary_range && (
                                    <div className="text-sm font-medium text-green-700">
                                        {application.job_listing.salary_range}
                                    </div>
                                )}
                                {application.job_listing.location && (
                                    <div className="text-sm text-gray-500">
                                        📍 {application.job_listing.location}
                                    </div>
                                )}
                            </div>
                            <div className="text-right space-y-1">
                                <Badge className={getStatusColor(application.application_status)} variant="outline">
                                    {application.application_status.charAt(0).toUpperCase() + application.application_status.slice(1)}
                                </Badge>
                            </div>
                        </div>

                        {/* Applied Date and AI Score */}
                        <div className="flex items-center justify-between pt-2 border-t border-gray-100">
                            <div className="flex items-center gap-2 text-sm text-gray-500">
                                <Calendar className="h-4 w-4" />
                                <span>Applied {formatDate(application.application_date)}</span>
                            </div>
                            {aiScore && (
                                <div className="flex items-center gap-2">
                                    <Brain className="h-4 w-4 text-purple-500" />
                                    <span className="text-sm font-medium text-purple-700">
                                        AI: {aiScore}%
                                    </span>
                                </div>
                            )}
                        </div>

                        {/* Quick Action */}
                        <div className="pt-2">
                            <Button
                                variant="outline"
                                size="sm"
                                className="w-full"
                                onClick={() => application.source_url && window.open(application.source_url, '_blank')}
                            >
                                <ExternalLink className="h-4 w-4 mr-2" />
                                View Job
                            </Button>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}

// Loading skeleton for cards
function JobCardSkeleton() {
    return (
        <Card className="h-full border border-gray-200 bg-white">
            <CardContent className="p-6">
                <div className="space-y-4">
                    <div className="space-y-2">
                        <div className="h-6 bg-gray-200 rounded animate-pulse"></div>
                        <div className="h-4 bg-gray-200 rounded w-3/4 animate-pulse"></div>
                    </div>
                    <div className="flex justify-between">
                        <div className="space-y-2">
                            <div className="h-4 bg-gray-200 rounded w-24 animate-pulse"></div>
                            <div className="h-3 bg-gray-200 rounded w-32 animate-pulse"></div>
                        </div>
                        <div className="h-6 bg-gray-200 rounded w-16 animate-pulse"></div>
                    </div>
                    <div className="flex justify-between pt-2 border-t border-gray-100">
                        <div className="h-4 bg-gray-200 rounded w-28 animate-pulse"></div>
                        <div className="h-4 bg-gray-200 rounded w-16 animate-pulse"></div>
                    </div>
                    <div className="h-8 bg-gray-200 rounded animate-pulse"></div>
                </div>
            </CardContent>
        </Card>
    )
}

export function AppliedJobsList({ userId, limit = 10 }: AppliedJobsListProps) {
    const [applications, setApplications] = useState<JobApplication[]>([])
    const [loading, setLoading] = useState(true)
    const [page, setPage] = useState(1)
    const [totalPages, setTotalPages] = useState(1)
    const [error, setError] = useState('')

    useEffect(() => {
        fetchApplications()
    }, [userId, page])

    const fetchApplications = async () => {
        try {
            setLoading(true)
            const response = await fetch(
                `${API_BASE_URL}/api/v1/jobs/applications/${userId}?page=${page}&limit=${limit}`
            )

            if (!response.ok) {
                throw new Error('Failed to fetch applications')
            }

            const data = await response.json()
            setApplications(data.applications || [])
            setTotalPages(Math.ceil((data.total || 0) / limit))
            setError('')
        } catch (err) {
            console.error('Error fetching applications:', err)
            setError('Failed to load applications')
            setApplications([])
        } finally {
            setLoading(false)
        }
    }

    if (error) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle>Recently Applied Jobs</CardTitle>
                    <CardDescription className="text-red-600">{error}</CardDescription>
                </CardHeader>
            </Card>
        )
    }

    return (
        <div className="space-y-6">
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Building className="h-5 w-5" />
                        Recently Applied Jobs
                    </CardTitle>
                    <CardDescription>
                        Track and manage your job applications. Total applications: {applications.length}
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    {applications.length === 0 && !loading ? (
                        <div className="text-center py-12">
                            <Building className="h-16 w-16 mx-auto text-gray-300 mb-4" />
                            <h3 className="text-lg font-medium text-gray-900 mb-2">No applications yet</h3>
                            <p className="text-gray-500 mb-6">
                                Start applying to jobs to see them here. You can extract jobs from URLs or browse our job listings.
                            </p>
                            <Button variant="outline" onClick={() => setPage(1)}>
                                Refresh
                            </Button>
                        </div>
                    ) : (
                        <>
                            {/* Grid layout with 3 columns */}
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                {loading ? (
                                    // Show loading skeletons
                                    <>
                                        <JobCardSkeleton />
                                        <JobCardSkeleton />
                                        <JobCardSkeleton />
                                        <JobCardSkeleton />
                                        <JobCardSkeleton />
                                        <JobCardSkeleton />
                                    </>
                                ) : (
                                    applications.map((application) => (
                                        <JobApplicationCard
                                            key={application.id}
                                            application={application}
                                        />
                                    ))
                                )}
                            </div>

                            {/* Pagination */}
                            {totalPages > 1 && (
                                <div className="flex items-center justify-between mt-6 pt-4 border-t">
                                    <p className="text-sm text-gray-600">
                                        Page {page} of {totalPages}
                                    </p>
                                    <div className="flex gap-2">
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => setPage(Math.max(1, page - 1))}
                                            disabled={page === 1}
                                        >
                                            Previous
                                        </Button>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => setPage(Math.min(totalPages, page + 1))}
                                            disabled={page === totalPages}
                                        >
                                            Next
                                        </Button>
                                    </div>
                                </div>
                            )}
                        </>
                    )}
                </CardContent>
            </Card>
        </div>
    )
}

// Add custom CSS for hiding scrollbar
const styles = `
.scrollbar-hide {
  -ms-overflow-style: none;  /* Internet Explorer 10+ */
  scrollbar-width: none;  /* Firefox */
}
.scrollbar-hide::-webkit-scrollbar { 
  display: none;  /* Safari and Chrome */
}
`

// Inject styles
if (typeof document !== 'undefined') {
    const styleSheet = document.createElement("style")
    styleSheet.innerText = styles
    document.head.appendChild(styleSheet)
} 