"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
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

// Mock data for applications
const mockApplications = [
    {
        id: "1",
        title: "Senior Frontend Developer",
        company: "TechCorp Inc.",
        location: "San Francisco, CA",
        salary: "$120,000 - $150,000",
        status: "applied",
        appliedDate: "2024-09-10",
        source: "LinkedIn",
        compatibilityScore: 92,
        notes: "Great company culture, remote friendly"
    },
    {
        id: "2",
        title: "Full Stack Engineer",
        company: "StartupXYZ",
        location: "New York, NY",
        salary: "$100,000 - $130,000",
        status: "interview_scheduled",
        appliedDate: "2024-09-08",
        source: "Indeed",
        compatibilityScore: 87,
        notes: "Interview scheduled for next week"
    },
    {
        id: "3",
        title: "Software Engineer",
        company: "BigTech Co.",
        location: "Seattle, WA",
        salary: "$110,000 - $140,000",
        status: "want_to_apply",
        appliedDate: null,
        source: "Company Website",
        compatibilityScore: 95,
        notes: "High priority - perfect match"
    },
    {
        id: "4",
        title: "DevOps Engineer",
        company: "Innovation Labs",
        location: "Austin, TX",
        salary: "$95,000 - $125,000",
        status: "not_interested",
        appliedDate: null,
        source: "AngelList",
        compatibilityScore: 78,
        notes: "Not a good cultural fit"
    }
]

const statusConfig = {
    applied: { label: "Applied", color: "bg-blue-500", icon: CheckCircle },
    interview_scheduled: { label: "Interview Scheduled", color: "bg-yellow-500", icon: Clock },
    want_to_apply: { label: "Want to Apply", color: "bg-green-500", icon: Target },
    not_interested: { label: "Not Interested", color: "bg-red-500", icon: X }
}

export default function ApplicationsPage() {
    const { user } = useAuth()
    const [applications, setApplications] = useState(mockApplications)
    const [searchTerm, setSearchTerm] = useState("")
    const [statusFilter, setStatusFilter] = useState("all")
    const [showJobExtractor, setShowJobExtractor] = useState(false)

    const filteredApplications = applications.filter(app => {
        const matchesSearch = app.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
            app.company.toLowerCase().includes(searchTerm.toLowerCase())
        const matchesStatus = statusFilter === "all" || app.status === statusFilter
        return matchesSearch && matchesStatus
    })

    const handleJobExtracted = (job: any) => {
        // Add the extracted job to applications
        const newApplication = {
            id: job.id,
            title: job.title,
            company: job.company,
            location: job.location,
            salary: "TBD",
            status: "want_to_apply",
            appliedDate: null,
            source: job.source || "URL Extraction",
            compatibilityScore: job.compatibilityScore || 0,
            notes: ""
        }
        setApplications(prev => [newApplication, ...prev])
        setShowJobExtractor(false)
    }

    const getStatusBadge = (status: string) => {
        const config = statusConfig[status as keyof typeof statusConfig]
        const Icon = config.icon
        return (
            <Badge className={`${config.color} text-white`}>
                <Icon className="w-3 h-3 mr-1" />
                {config.label}
            </Badge>
        )
    }

    return (
        <div className="space-y-4 sm:space-y-6">
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

            {/* Stats Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
                <Card className="bg-primary-900 border-l-4 border-l-blue-500">
                    <CardContent className="p-4">
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
                    <CardContent className="p-4">
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
                    <CardContent className="p-4">
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
                    <CardContent className="p-4">
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
                <CardContent className="p-3 sm:p-4">
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
            <div className="space-y-4">
                {filteredApplications.map((application) => (
                    <Card key={application.id} className="hover:shadow-lg transition-shadow">
                        <CardContent className="p-6">
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
                                            {application.appliedDate
                                                ? `Applied ${new Date(application.appliedDate).toLocaleDateString()}`
                                                : "Not applied yet"
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
                                    <Button variant="outline" size="sm">
                                        <ExternalLink className="w-4 h-4 mr-1" />
                                        View
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

            {filteredApplications.length === 0 && (
                <Card className="bg-primary-900">
                    <CardContent className="flex flex-col items-center justify-center py-12">
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
        </div>
    )
}
