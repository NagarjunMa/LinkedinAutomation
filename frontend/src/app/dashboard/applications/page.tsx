"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import JobURLExtractor from "@/components/job-url-extractor"
import {
    Search,
    Plus,
    Filter,
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
import { fetchRecentApplications } from "@/app/lib/api"
import { useToast } from "@/components/ui/use-toast"

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
    const [applications, setApplications] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [searchTerm, setSearchTerm] = useState("")
    const [statusFilter, setStatusFilter] = useState("all")
    const [showJobExtractor, setShowJobExtractor] = useState(false)
    const [selectedJob, setSelectedJob] = useState<any>(null)
    const [showJobDetails, setShowJobDetails] = useState(false)
    const [jobDetails, setJobDetails] = useState<any>(null)
    const [loadingJobDetails, setLoadingJobDetails] = useState(false)

    // Fetch real applications data
    const fetchApplications = async () => {
        try {
            setLoading(true)
            const data = await fetchRecentApplications(50) // Get more applications

            // Map backend data to frontend format
            const mappedApplications = data.map((app: any) => ({
                id: app.id,
                title: app.title || 'Unknown Position',
                company: app.company || 'Unknown Company',
                location: app.location || 'Remote',
                salary: 'TBD', // Backend doesn't return salary in recent-applications
                status: app.status?.toLowerCase().replace(' ', '_') || 'applied',
                appliedDate: app.applied_date ? app.applied_date.split('T')[0] : null,
                source: app.application_source === 'url_extraction' ? 'URL Extraction' : (app.application_source || 'Manual'),
                compatibilityScore: 0, // Backend doesn't return this in recent-applications
                notes: '',
                sourceUrl: app.source_url
            }))

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
    }

    // Load applications on component mount
    useEffect(() => {
        fetchApplications()
    }, [])

    const filteredApplications = applications.filter(app => {
        const matchesSearch = app.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
            app.company.toLowerCase().includes(searchTerm.toLowerCase())
        const matchesStatus = statusFilter === "all" || app.status === statusFilter
        return matchesSearch && matchesStatus
    })

    const handleJobExtracted = async (job: any) => {
        // Show success message
        toast({
            title: "Success!",
            description: `Successfully extracted: ${job.extracted_job?.title || job.title} at ${job.extracted_job?.company || job.company}`,
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

            const jobDetails = await response.json()
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

    const handleViewJob = (application: any) => {
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

    return (
        <div className="px-4 sm:px-6 lg:px-8 space-y-4 sm:space-y-6">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl sm:text-3xl font-bold text-cream-50">Job Applications</h1>
                    <p className="text-cream-300 mt-1 text-sm sm:text-base">
                        Track and manage your job applications with AI-powered insights
                    </p>
                </div>
                <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
                    <Button
                        onClick={() => setShowJobExtractor(true)}
                        className="bg-gradient-to-r from-orange-600 to-orange-500 hover:from-orange-700 hover:to-orange-600 w-full sm:w-auto"
                    >
                        <Plus className="w-4 h-4 mr-2" />
                        Extract Job URL
                    </Button>
                    <Button variant="outline" className="w-full sm:w-auto border-cream-300 text-cream-50 hover:bg-primary-800">
                        <Download className="w-4 h-4 mr-2" />
                        Export
                    </Button>
                </div>
            </div>

            {/* Loading State */}
            {loading && (
                <div className="flex items-center justify-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500 mr-3"></div>
                    <span className="text-cream-300">Loading applications...</span>
                </div>
            )}

            {/* Stats Cards */}
            {!loading && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
                <Card className="bg-primary-900 border-l-4 border-l-blue-500">
                    <CardContent className="p-4 sm:p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-cream-300">Total Applications</p>
                                <p className="text-2xl font-bold text-cream-50">{applications.length}</p>
                            </div>
                            <Briefcase className="w-8 h-8 text-blue-500" />
                        </div>
                    </CardContent>
                </Card>
                <Card className="bg-primary-900 border-l-4 border-l-green-500">
                    <CardContent className="p-4 sm:p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-cream-300">Applied</p>
                                <p className="text-2xl font-bold text-cream-50">
                                    {applications.filter(app => app.status === 'applied').length}
                                </p>
                            </div>
                            <CheckCircle className="w-8 h-8 text-green-500" />
                        </div>
                    </CardContent>
                </Card>
                <Card className="bg-primary-900 border-l-4 border-l-yellow-500">
                    <CardContent className="p-4 sm:p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-cream-300">Interviews</p>
                                <p className="text-2xl font-bold text-cream-50">
                                    {applications.filter(app => app.status === 'interview_scheduled').length}
                                </p>
                            </div>
                            <Clock className="w-8 h-8 text-yellow-500" />
                        </div>
                    </CardContent>
                </Card>
                <Card className="bg-primary-900 border-l-4 border-l-purple-500">
                    <CardContent className="p-4 sm:p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-cream-300">Avg. Score</p>
                                <p className="text-2xl font-bold text-cream-50">
                                    {Math.round(applications.reduce((acc, app) => acc + app.compatibilityScore, 0) / applications.length)}%
                                </p>
                            </div>
                            <TrendingUp className="w-8 h-8 text-purple-500" />
                        </div>
                    </CardContent>
                </Card>
            </div>
            )}

            {/* Job URL Extractor Modal */}
            {showJobExtractor && (
                <Card className="border-2 border-orange-500/50 bg-primary-800">
                    <CardHeader>
                        <div className="flex items-center justify-between">
                            <CardTitle className="text-cream-50">Extract Job from URL</CardTitle>
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setShowJobExtractor(false)}
                                className="text-cream-300 hover:text-cream-50"
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
            <Card>
                <CardContent className="p-4 sm:p-6">
                    <div className="flex flex-col sm:flex-row gap-3 sm:gap-4">
                        <div className="flex-1">
                            <Label htmlFor="search" className="text-sm">Search Applications</Label>
                            <div className="relative">
                                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                                <Input
                                    id="search"
                                    placeholder="Search by job title or company..."
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                    className="pl-10 text-sm"
                                />
                            </div>
                        </div>
                        <div className="sm:w-48">
                            <Label htmlFor="status-filter" className="text-sm">Filter by Status</Label>
                            <select
                                id="status-filter"
                                value={statusFilter}
                                onChange={(e) => setStatusFilter(e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md bg-white text-gray-900 text-sm"
                            >
                                <option value="all">All Statuses</option>
                                <option value="applied">Applied</option>
                                <option value="interview_scheduled">Interview Scheduled</option>
                                <option value="want_to_apply">Want to Apply</option>
                                <option value="not_interested">Not Interested</option>
                            </select>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Applications List */}
            {!loading && (
            <div className="space-y-4">
                {filteredApplications.map((application) => (
                    <Card key={application.id} className="hover:shadow-lg transition-shadow">
                        <CardContent className="p-4 sm:p-6">
                            <div className="flex items-start justify-between">
                                <div className="flex-1">
                                    <div className="flex items-center gap-3 mb-2">
                                        <h3 className="text-xl font-semibold text-cream-50">
                                            {application.title}
                                        </h3>
                                        {getStatusBadge(application.status)}
                                    </div>
                                    <div className="flex items-center gap-4 text-cream-300 mb-3">
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
                                    <div className="flex items-center gap-4 text-sm text-cream-400">
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
                                        <div className="mt-3 p-3 bg-primary-800 rounded-lg border border-primary-600">
                                            <p className="text-sm text-cream-200">
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
                <Card className="bg-primary-900">
                    <CardContent className="flex flex-col items-center justify-center py-12 px-4 sm:px-6">
                        <Briefcase className="w-16 h-16 text-cream-400 mb-4" />
                        <h3 className="text-lg font-semibold text-cream-300 mb-2">
                            No applications found
                        </h3>
                        <p className="text-cream-400 text-center mb-4">
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
                                    <h3 className="font-semibold text-cream-50">Job Type</h3>
                                    <p className="text-cream-300">{jobDetails.job_type || 'Not specified'}</p>
                                </div>
                                <div className="space-y-2">
                                    <h3 className="font-semibold text-cream-50">Experience Level</h3>
                                    <p className="text-cream-300">{jobDetails.experience_level || 'Not specified'}</p>
                                </div>
                                <div className="space-y-2">
                                    <h3 className="font-semibold text-cream-50">Salary Range</h3>
                                    <p className="text-cream-300">{jobDetails.salary_range || 'Not disclosed'}</p>
                                </div>
                                <div className="space-y-2">
                                    <h3 className="font-semibold text-cream-50">Posted Date</h3>
                                    <p className="text-cream-300">
                                        {jobDetails.posted_date ? new Date(jobDetails.posted_date).toLocaleDateString() : 'Unknown'}
                                    </p>
                                </div>
                            </div>

                            {/* Job Description */}
                            {jobDetails.description && (
                                <div className="space-y-2">
                                    <h3 className="font-semibold text-cream-50">Job Description</h3>
                                    <div className="bg-primary-800 p-4 rounded-lg border border-primary-600">
                                        <p className="text-cream-200 whitespace-pre-wrap">{jobDetails.description}</p>
                                    </div>
                                </div>
                            )}

                            {/* Requirements */}
                            {jobDetails.requirements && (
                                <div className="space-y-2">
                                    <h3 className="font-semibold text-cream-50">Requirements</h3>
                                    <div className="bg-primary-800 p-4 rounded-lg border border-primary-600">
                                        <p className="text-cream-200 whitespace-pre-wrap">{jobDetails.requirements}</p>
                                    </div>
                                </div>
                            )}

                            {/* Skills */}
                            {jobDetails.skills && (
                                <div className="space-y-2">
                                    <h3 className="font-semibold text-cream-50">Required Skills</h3>
                                    <div className="bg-primary-800 p-4 rounded-lg border border-primary-600">
                                        <p className="text-cream-200 whitespace-pre-wrap">{jobDetails.skills}</p>
                                    </div>
                                </div>
                            )}

                            {/* Benefits */}
                            {jobDetails.benefits && (
                                <div className="space-y-2">
                                    <h3 className="font-semibold text-cream-50">Benefits</h3>
                                    <div className="bg-primary-800 p-4 rounded-lg border border-primary-600">
                                        <p className="text-cream-200 whitespace-pre-wrap">{jobDetails.benefits}</p>
                                    </div>
                                </div>
                            )}

                            {/* Action Buttons */}
                            <div className="flex gap-3 pt-4 border-t border-primary-600">
                                <Button
                                    onClick={() => window.open(jobDetails.application_url, '_blank')}
                                    className="bg-gradient-to-r from-orange-600 to-orange-500 hover:from-orange-700 hover:to-orange-600"
                                >
                                    <ExternalLink className="w-4 h-4 mr-2" />
                                    Apply Now
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
