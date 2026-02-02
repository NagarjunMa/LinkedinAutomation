"use client"

import { useState, useEffect, useCallback } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import JobURLExtractor from "@/components/job-url-extractor"
import {
    Search,
    Plus,
    Download,
    ExternalLink,
    CheckCircle,
    Clock,
    X,
    Target,
    Briefcase,
    Calendar,
    MapPin,
    DollarSign,
    Users,
    TrendingUp
} from "lucide-react"
import { useAuth } from "@/contexts/auth-context"
import { fetchRecentApplications } from "@/app/lib/api/jobs"
import { useToast } from "@/components/ui/use-toast"

type RecentApplicationResponse = Awaited<ReturnType<typeof fetchRecentApplications>>[number]

type ApplicationStatus = 'applied' | 'interview_scheduled' | 'want_to_apply' | 'not_interested' | string

interface Application {
    id: string;
    title: string;
    company: string;
    location: string;
    salary: string;
    status: ApplicationStatus;
    appliedDate: string | null;
    source: string;
    compatibilityScore: number;
    notes: string;
    sourceUrl?: string;
    extractedAt?: string;
}

interface JobDetails {
    id?: string;
    title?: string;
    company?: string;
    location?: string;
    job_type?: string;
    experience_level?: string;
    salary_range?: string;
    posted_date?: string;
    description?: string;
    requirements?: string;
    skills?: string;
    benefits?: string;
    application_url?: string;
}

interface ExtractedJobPayload {
    job_id?: string;
    id?: string;
    extracted_job?: {
        title?: string;
        company?: string;
        location?: string;
        application_url?: string;
    };
    title?: string;
    company?: string;
    location?: string;
    original_url?: string;
}

const normalizeStatus = (status?: string): ApplicationStatus => {
    if (!status) return 'applied'
    return status.toLowerCase().replace(/\s+/g, '_')
}

const deriveSource = (source?: string) => {
    if (!source) return 'Manual'
    if (source === 'url_extraction') return 'URL Extraction'
    return source
}

const mapRecentApplication = (app: RecentApplicationResponse): Application => ({
    id: app.id,
    title: app.title || 'Unknown Position',
    company: app.company || 'Unknown Company',
    location: app.location || 'Remote',
    salary: app.salary || 'TBD',
    status: normalizeStatus(app.status),
    appliedDate: app.appliedAt ? app.appliedAt.split('T')[0] : null,
    source: deriveSource(app.applicationSource),
    compatibilityScore: app.compatibilityScore || 0,
    notes: '',
    sourceUrl: app.sourceUrl
})

// Application status configuration
const statusConfig = {
    applied: { label: "Applied", color: "bg-blue-500", icon: CheckCircle },
    interview_scheduled: { label: "Interview Scheduled", color: "bg-yellow-500", icon: Clock },
    want_to_apply: { label: "Want to Apply", color: "bg-green-500", icon: Target },
    not_interested: { label: "Not Interested", color: "bg-red-500", icon: X }
}

export default function ApplicationsPage() {
    const { user } = useAuth()
    const { toast } = useToast()
    const [applications, setApplications] = useState<Application[]>([])
    const [loading, setLoading] = useState(true)
    const [searchTerm, setSearchTerm] = useState("")
    const [statusFilter, setStatusFilter] = useState("all")
    const [showJobExtractor, setShowJobExtractor] = useState(false)
    const [selectedJob, setSelectedJob] = useState<Application | null>(null)
    const [showJobDetails, setShowJobDetails] = useState(false)
    const [jobDetails, setJobDetails] = useState<JobDetails | null>(null)
    const [loadingJobDetails, setLoadingJobDetails] = useState(false)
    const [recentlyExtractedJob, setRecentlyExtractedJob] = useState<Application | null>(null)

    // Fetch real applications data
    const fetchApplications = useCallback(async () => {
        try {
            setLoading(true)
            const data = await fetchRecentApplications(50) // Get more applications

            // Map backend data to frontend format
            const mappedApplications = data.map(mapRecentApplication)

            setApplications(mappedApplications)
        } catch (error) {
            console.error('Failed to fetch applications:', error)
            // Show empty state instead of mock data
            setApplications([])
            toast({
                title: "Error",
                description: "Could not load your applications. Please try again later.",
                variant: "destructive",
            })
        } finally {
            setLoading(false)
        }
    }, [toast])

    // Load applications on component mount
    useEffect(() => {
        fetchApplications()
    }, [fetchApplications])

    const filteredApplications = applications.filter(app => {
        const matchesSearch = app.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
            app.company.toLowerCase().includes(searchTerm.toLowerCase())
        const matchesStatus = statusFilter === "all" || app.status === statusFilter
        return matchesSearch && matchesStatus
    })

    const averageCompatibilityScore = applications.length
        ? Math.round(applications.reduce((acc, app) => acc + app.compatibilityScore, 0) / applications.length)
        : 0

    const handleJobExtracted = async (job: ExtractedJobPayload) => {
        const fallbackId = job.job_id || job.id || (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
            ? crypto.randomUUID()
            : `${Date.now()}`)
        // Store recently extracted job for immediate feedback
        const extractedJobData: Application = {
            id: String(fallbackId),
            title: job.extracted_job?.title || job.title || 'Unknown Position',
            company: job.extracted_job?.company || job.company || 'Unknown Company',
            location: job.extracted_job?.location || job.location || 'Remote',
            salary: 'TBD',
            status: 'applied',
            appliedDate: new Date().toISOString(),
            source: 'URL Extraction',
            compatibilityScore: 0,
            notes: '',
            sourceUrl: job.extracted_job?.application_url || job.original_url,
            extractedAt: new Date().toISOString()
        }
        setRecentlyExtractedJob(extractedJobData)

        // Show success message
        toast({
            title: "Job Extracted Successfully!",
            description: `${extractedJobData.title} at ${extractedJobData.company}`,
        })

        // Refresh the applications list to show the new extraction
        await fetchApplications()
        setShowJobExtractor(false)
    }

    // Fetch detailed job information
    const fetchJobDetails = async (jobId: string) => {
        try {
            setLoadingJobDetails(true)
            const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
            const response = await fetch(`${API_BASE_URL}/api/v1/jobs/${jobId}`)

            if (!response.ok) {
                throw new Error('Failed to fetch job details')
            }

            const jobDetails: JobDetails = await response.json()
            setJobDetails(jobDetails)
            setShowJobDetails(true)
        } catch (error) {
            console.error('Failed to fetch job details:', error)
            toast({
                title: "Error",
                description: "Failed to load job details",
                variant: "destructive",
            })
        } finally {
            setLoadingJobDetails(false)
        }
    }

    const handleViewJob = (application: Application) => {
        setSelectedJob(application)
        fetchJobDetails(application.id)
    }

    const getStatusBadge = (status: string) => {
        const config = statusConfig[status as keyof typeof statusConfig]

        // Fallback for unknown statuses
        if (!config) {
            return (
                <Badge className="bg-gray-500 text-white">
                    <CheckCircle className="w-3 h-3 mr-1" />
                    {status || 'Unknown'}
                </Badge>
            )
        }

        const Icon = config.icon
        return (
            <Badge className={`${config.color} text-white`}>
                <Icon className="w-3 h-3 mr-1" />
                {config.label}
            </Badge>
        )
    }

    // Recently Extracted Job Card Component
    const RecentlyExtractedJobCard = () => {
        if (!recentlyExtractedJob) return null

        return (
            <Card className="bg-gradient-to-r from-green-900/20 to-blue-900/20 border border-green-500/30">
                <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                            <CheckCircle className="w-5 h-5 text-green-400" />
                            <CardTitle className="text-lg text-foreground">Recently Extracted Job</CardTitle>
                        </div>
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setRecentlyExtractedJob(null)}
                        >
                            <X className="w-4 h-4" />
                        </Button>
                    </div>
                    <CardDescription className="text-muted-foreground">
                        Job successfully extracted from URL
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="space-y-3">
                        <div>
                            <h3 className="font-semibold text-foreground">{recentlyExtractedJob.title}</h3>
                            <p className="text-muted-foreground">{recentlyExtractedJob.company}</p>
                            {recentlyExtractedJob.location && (
                                <div className="flex items-center text-sm text-muted-foreground mt-1">
                                    <MapPin className="w-3 h-3 mr-1" />
                                    {recentlyExtractedJob.location}
                                </div>
                            )}
                        </div>
                        <div className="flex gap-2">
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleViewJob(recentlyExtractedJob)}
                                className="flex-1"
                            >
                                <Briefcase className="w-4 h-4 mr-2" />
                                View Details
                            </Button>
                            {recentlyExtractedJob.sourceUrl && (
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => window.open(recentlyExtractedJob.sourceUrl, '_blank')}
                                    className="flex-1"
                                >
                                    <ExternalLink className="w-4 h-4 mr-2" />
                                    Go to Job
                                </Button>
                            )}
                        </div>
                    </div>
                </CardContent>
            </Card>
        )
    }

    return (
        <div className="min-h-screen bg-background px-4 sm:px-6 lg:px-8 py-8 space-y-8 font-sans text-foreground">
            <div className="fixed inset-0 pointer-events-none opacity-[0.015]"
                style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")` }}
            />

            {/* Header */}
            <div className="relative flex flex-col sm:flex-row sm:items-center justify-between gap-6">
                <div>
                    <h1 className="text-4xl font-black text-foreground tracking-tight uppercase">Job Applications</h1>
                    <p className="text-muted-foreground mt-2 text-base font-medium max-w-2xl">
                        Track and manage your job applications with AI-powered insights
                    </p>
                </div>
                <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4">
                    <Button
                        onClick={() => setShowJobExtractor(true)}
                        className="px-8 py-6 bg-primary text-primary-foreground rounded-2xl font-black text-xs uppercase tracking-widest shadow-xl hover:bg-primary/90 transition-all active:scale-95"
                    >
                        <Plus className="w-4 h-4 mr-2" />
                        Extract Job URL
                    </Button>
                    <Button
                        variant="outline"
                        className="px-8 py-6 bg-card/80 backdrop-blur-md border border-border shadow-sm rounded-2xl font-black text-xs uppercase tracking-widest text-foreground hover:bg-accent transition-all"
                    >
                        <Download className="w-4 h-4 mr-2" />
                        Export
                    </Button>
                </div>
            </div>

            {/* Loading State */}
            {loading && (
                <div className="flex items-center justify-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mr-3"></div>
                    <span className="text-muted-foreground font-medium">Loading applications...</span>
                </div>
            )}

            {/* Recently Extracted Job Card */}
            <RecentlyExtractedJobCard />

            {/* Stats Cards */}
            {!loading && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 sm:gap-6">
                    <Card className="bg-card p-6 rounded-[32px] border border-border shadow-sm hover:shadow-xl transition-all">
                        <CardContent className="p-0">
                            <div className="flex flex-col justify-between h-full space-y-4">
                                <div className="flex items-start justify-between">
                                    <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-2xl">
                                        <Briefcase className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                                    </div>
                                    <span className="text-[10px] font-black uppercase tracking-widest text-muted-foreground bg-muted px-2 py-1 rounded-full">Total</span>
                                </div>
                                <div>
                                    <p className="text-3xl font-black text-foreground">{applications.length}</p>
                                    <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider mt-1">Applications</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                    <Card className="bg-card p-6 rounded-[32px] border border-border shadow-sm hover:shadow-xl transition-all">
                        <CardContent className="p-0">
                            <div className="flex flex-col justify-between h-full space-y-4">
                                <div className="flex items-start justify-between">
                                    <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-2xl">
                                        <CheckCircle className="w-6 h-6 text-green-600 dark:text-green-400" />
                                    </div>
                                    <span className="text-[10px] font-black uppercase tracking-widest text-muted-foreground bg-muted px-2 py-1 rounded-full">Active</span>
                                </div>
                                <div>
                                    <p className="text-3xl font-black text-foreground">
                                        {applications.filter(app => app.status === 'applied').length}
                                    </p>
                                    <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider mt-1">Applied</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                    <Card className="bg-card p-6 rounded-[32px] border border-border shadow-sm hover:shadow-xl transition-all">
                        <CardContent className="p-0">
                            <div className="flex flex-col justify-between h-full space-y-4">
                                <div className="flex items-start justify-between">
                                    <div className="p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-2xl">
                                        <Clock className="w-6 h-6 text-yellow-600 dark:text-yellow-400" />
                                    </div>
                                    <span className="text-[10px] font-black uppercase tracking-widest text-muted-foreground bg-muted px-2 py-1 rounded-full">Interview</span>
                                </div>
                                <div>
                                    <p className="text-3xl font-black text-foreground">
                                        {applications.filter(app => app.status === 'interview_scheduled').length}
                                    </p>
                                    <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider mt-1">Scheduled</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                    <Card className="bg-card p-6 rounded-[32px] border border-border shadow-sm hover:shadow-xl transition-all">
                        <CardContent className="p-0">
                            <div className="flex flex-col justify-between h-full space-y-4">
                                <div className="flex items-start justify-between">
                                    <div className="p-3 bg-purple-50 dark:bg-purple-900/20 rounded-2xl">
                                        <TrendingUp className="w-6 h-6 text-purple-600 dark:text-purple-400" />
                                    </div>
                                    <span className="text-[10px] font-black uppercase tracking-widest text-muted-foreground bg-muted px-2 py-1 rounded-full">Score</span>
                                </div>
                                <div>
                                    <p className="text-3xl font-black text-foreground">
                                        {averageCompatibilityScore}%
                                    </p>
                                    <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider mt-1">Avg Match</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            )}

            {/* Job URL Extractor Modal */}
            {showJobExtractor && (
                <Card className="border-2 border-orange-500/50 bg-card">
                    <CardHeader>
                        <div className="flex items-center justify-between">
                            <CardTitle className="text-foreground">Extract Job from URL</CardTitle>
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setShowJobExtractor(false)}
                                className="text-muted-foreground hover:text-foreground"
                            >
                                <X className="w-4 h-4" />
                            </Button>
                        </div>
                    </CardHeader>
                    <CardContent>
                        <JobURLExtractor
                            userId={user?.id || "demo_user"}
                            onJobExtracted={handleJobExtracted}
                        />
                    </CardContent>
                </Card>
            )}

            {/* Filters and Search */}
            <Card className="bg-card p-6 rounded-[32px] border border-border shadow-sm">
                <CardContent className="p-0">
                    <div className="flex flex-col sm:flex-row gap-4 sm:gap-6">
                        <div className="flex-1">
                            <Label htmlFor="search" className="text-xs font-bold text-foreground uppercase tracking-wider mb-2 block">Search Applications</Label>
                            <div className="relative">
                                <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
                                <Input
                                    id="search"
                                    placeholder="Search by job title or company..."
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                    className="pl-11 h-12 bg-muted/50 border-input rounded-xl text-sm focus:ring-primary focus:border-primary"
                                />
                            </div>
                        </div>
                        <div className="sm:w-64">
                            <Label htmlFor="status-filter" className="text-xs font-bold text-foreground uppercase tracking-wider mb-2 block">Filter by Status</Label>
                            <div className="relative">
                                <select
                                    id="status-filter"
                                    value={statusFilter}
                                    onChange={(e) => setStatusFilter(e.target.value)}
                                    className="w-full h-12 px-4 bg-muted/50 border border-input rounded-xl text-sm text-foreground focus:ring-primary focus:border-primary appearance-none"
                                >
                                    <option value="all">All Statuses</option>
                                    <option value="applied">Applied</option>
                                    <option value="interview_scheduled">Interview Scheduled</option>
                                    <option value="want_to_apply">Want to Apply</option>
                                    <option value="not_interested">Not Interested</option>
                                </select>
                                <div className="absolute right-4 top-1/2 transform -translate-y-1/2 pointer-events-none">
                                    <svg className="w-4 h-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                    </svg>
                                </div>
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Applications List */}
            {!loading && (
                <div className="space-y-4">
                    {filteredApplications.map((application) => (
                        <Card key={application.id} className="hover:shadow-lg transition-shadow bg-card border-border">
                            <CardContent className="p-4 sm:p-6">
                                <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                        <div className="flex items-center gap-3 mb-2">
                                            <h3 className="text-xl font-semibold text-foreground">
                                                {application.title}
                                            </h3>
                                            {getStatusBadge(application.status)}
                                        </div>
                                        <div className="flex items-center gap-4 text-muted-foreground mb-3">
                                            <div className="flex items-center gap-1">
                                                <Users className="w-4 h-4" />
                                                {application.company}
                                            </div>
                                            <div className="flex items-center gap-1">
                                                <MapPin className="w-4 h-4" />
                                                {application.location}
                                            </div>
                                            <div className="flex items-center gap-1">
                                                <DollarSign className="w-4 h-4" />
                                                {application.salary}
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-4 text-sm text-muted-foreground">
                                            <div className="flex items-center gap-1">
                                                <Calendar className="w-4 h-4" />
                                                {application.status === 'applied' || application.appliedDate
                                                    ? `Applied ${application.appliedDate ? new Date(application.appliedDate).toLocaleDateString() : 'recently'}`
                                                    : application.status === 'want_to_apply'
                                                        ? "Want to apply"
                                                        : application.status === 'interview_scheduled'
                                                            ? "Interview scheduled"
                                                            : application.status === 'not_interested'
                                                                ? "Not interested"
                                                                : "Status unknown"
                                                }
                                            </div>
                                            <div className="flex items-center gap-1">
                                                <ExternalLink className="w-4 h-4" />
                                                {application.source}
                                            </div>
                                            {application.compatibilityScore > 0 && (
                                                <div className="flex items-center gap-1">
                                                    <TrendingUp className="w-4 h-4" />
                                                    {application.compatibilityScore}% match
                                                </div>
                                            )}
                                        </div>
                                        {application.notes && (
                                            <div className="mt-3 p-3 bg-muted rounded-lg border border-border">
                                                <p className="text-sm text-muted-foreground">
                                                    <strong>Notes:</strong> {application.notes}
                                                </p>
                                            </div>
                                        )}
                                    </div>
                                    <div className="flex items-center gap-2 ml-4">
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => handleViewJob(application)}
                                            disabled={loadingJobDetails}
                                        >
                                            {loadingJobDetails && selectedJob?.id === application.id ? (
                                                <div className="flex items-center gap-1">
                                                    <div className="w-3 h-3 animate-spin rounded-full border border-gray-300 border-t-gray-600"></div>
                                                    Loading...
                                                </div>
                                            ) : (
                                                <div className="flex items-center gap-1">
                                                    <ExternalLink className="w-4 h-4" />
                                                    View
                                                </div>
                                            )}
                                        </Button>
                                        <Button variant="outline" size="sm">
                                            Edit
                                        </Button>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            )}

            {!loading && filteredApplications.length === 0 && (
                <Card className="bg-card border-border">
                    <CardContent className="flex flex-col items-center justify-center py-12 px-4 sm:px-6">
                        <Briefcase className="w-16 h-16 text-muted-foreground mb-4" />
                        <h3 className="text-lg font-semibold text-foreground mb-2">
                            No applications found
                        </h3>
                        <p className="text-muted-foreground text-center mb-4">
                            {searchTerm || statusFilter !== "all"
                                ? "Try adjusting your search or filter criteria"
                                : "Start by extracting a job from a URL or adding an application manually"
                            }
                        </p>
                        <Button
                            onClick={() => setShowJobExtractor(true)}
                            className="bg-gradient-to-r from-orange-600 to-orange-500 hover:from-orange-700 hover:to-orange-600"
                        >
                            <Plus className="w-4 h-4 mr-2" />
                            Extract Job URL
                        </Button>
                    </CardContent>
                </Card>
            )}

            {/* Job Details Modal */}
            <Dialog open={showJobDetails} onOpenChange={setShowJobDetails}>
                <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
                    <DialogHeader>
                        <DialogTitle className="text-xl font-bold">
                            {jobDetails?.title || 'Job Details'}
                        </DialogTitle>
                        <DialogDescription>
                            {jobDetails?.company} • {jobDetails?.location}
                        </DialogDescription>
                    </DialogHeader>

                    {jobDetails && (
                        <div className="space-y-6">
                            {/* Job Overview */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <h3 className="font-semibold text-foreground">Job Type</h3>
                                    <p className="text-muted-foreground">{jobDetails.job_type || 'Not specified'}</p>
                                </div>
                                <div className="space-y-2">
                                    <h3 className="font-semibold text-foreground">Experience Level</h3>
                                    <p className="text-muted-foreground">{jobDetails.experience_level || 'Not specified'}</p>
                                </div>
                                <div className="space-y-2">
                                    <h3 className="font-semibold text-foreground">Salary Range</h3>
                                    <p className="text-muted-foreground">{jobDetails.salary_range || 'Not disclosed'}</p>
                                </div>
                                <div className="space-y-2">
                                    <h3 className="font-semibold text-foreground">Posted Date</h3>
                                    <p className="text-muted-foreground">
                                        {jobDetails.posted_date ? new Date(jobDetails.posted_date).toLocaleDateString() : 'Unknown'}
                                    </p>
                                </div>
                            </div>

                            {/* Job Description */}
                            {jobDetails.description && (
                                <div className="space-y-2">
                                    <h3 className="font-semibold text-foreground">Job Description</h3>
                                    <div className="bg-muted p-4 rounded-lg border border-border">
                                        <p className="text-muted-foreground whitespace-pre-wrap">{jobDetails.description}</p>
                                    </div>
                                </div>
                            )}

                            {/* Requirements */}
                            {jobDetails.requirements && (
                                <div className="space-y-2">
                                    <h3 className="font-semibold text-foreground">Requirements</h3>
                                    <div className="bg-muted p-4 rounded-lg border border-border">
                                        <p className="text-muted-foreground whitespace-pre-wrap">{jobDetails.requirements}</p>
                                    </div>
                                </div>
                            )}

                            {/* Skills */}
                            {jobDetails.skills && (
                                <div className="space-y-2">
                                    <h3 className="font-semibold text-foreground">Required Skills</h3>
                                    <div className="bg-muted p-4 rounded-lg border border-border">
                                        <p className="text-muted-foreground whitespace-pre-wrap">{jobDetails.skills}</p>
                                    </div>
                                </div>
                            )}

                            {/* Benefits */}
                            {jobDetails.benefits && (
                                <div className="space-y-2">
                                    <h3 className="font-semibold text-foreground">Benefits</h3>
                                    <div className="bg-muted p-4 rounded-lg border border-border">
                                        <p className="text-muted-foreground whitespace-pre-wrap">{jobDetails.benefits}</p>
                                    </div>
                                </div>
                            )}

                            {/* Action Buttons */}
                            <div className="flex gap-3 pt-4 border-t border-border">
                                <Button
                                    onClick={() => jobDetails.application_url && window.open(jobDetails.application_url, '_blank')}
                                    disabled={!jobDetails.application_url}
                                    className="bg-gradient-to-r from-orange-600 to-orange-500 hover:from-orange-700 hover:to-orange-600 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    <ExternalLink className="w-4 h-4 mr-2" />
                                    {jobDetails.application_url ? 'Apply Now' : 'Application URL missing'}
                                </Button>
                                <Button
                                    variant="outline"
                                    onClick={() => setShowJobDetails(false)}
                                >
                                    Close
                                </Button>
                            </div>
                        </div>
                    )}
                </DialogContent>
            </Dialog>
        </div>
    )
}
