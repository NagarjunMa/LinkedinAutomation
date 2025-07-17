"use client"

import { useEffect, useState } from "react"
import { fetchJobs, updateJobStatus } from "@/app/lib/api"
import type { Job, JobFilters } from "../types/job"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { useToast } from "@/components/ui/use-toast"
import { Badge } from "@/components/ui/badge"
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card"
import { format, isValid, parseISO } from "date-fns"
import { CalendarIcon, FilterIcon, RefreshCwIcon } from "lucide-react"

// Job interface imported from types/job.ts

const formatDate = (dateString: string) => {
    try {
        const date = parseISO(dateString)
        if (isValid(date)) {
            return format(date, 'MMM dd, yyyy')
        }
    } catch (error) {
        console.warn('Error formatting date:', dateString)
    }
    return 'Invalid date'
}

export default function JobsPage() {
    const [jobs, setJobs] = useState<Job[]>([])
    const [loading, setLoading] = useState(true)
    const [filters, setFilters] = useState<JobFilters & { applicationStatus: string }>({
        sortBy: 'newest',
        applicationStatus: 'all'
    })
    const { toast } = useToast()

    useEffect(() => {
        const loadJobs = async () => {
            try {
                setLoading(true)
                const data = await fetchJobs(filters)

                // Filter by application status on frontend
                let filteredData = data
                if (filters.applicationStatus === 'applied') {
                    filteredData = data.filter((job: Job) => job.applied)
                } else if (filters.applicationStatus === 'not-applied') {
                    filteredData = data.filter((job: Job) => !job.applied)
                }

                setJobs(filteredData)
            } catch (error) {
                console.error('Failed to fetch jobs:', error)
                toast({
                    title: "Error",
                    description: "Failed to fetch jobs",
                    variant: "destructive",
                })
            } finally {
                setLoading(false)
            }
        }
        loadJobs()
    }, [filters, toast])

    const handleFilterChange = (key: keyof (JobFilters & { applicationStatus: string }), value: string) => {
        setFilters(prev => ({ ...prev, [key]: value }))
    }

    const handleStatusChange = async (jobId: string, applied: boolean) => {
        try {
            await updateJobStatus(jobId, applied)
            setJobs(jobs.map(job =>
                job.id === jobId ? { ...job, applied } : job
            ))

            toast({
                title: "Success",
                description: `Job marked as ${applied ? 'applied' : 'not applied'}`,
            })
        } catch (error) {
            console.error('Failed to update job status:', error)
            toast({
                title: "Error",
                description: "Failed to update job status",
                variant: "destructive",
            })
        }
    }

    const refreshJobs = () => {
        setFilters(prev => ({ ...prev }))
    }

    const getStatsDisplay = () => {
        const total = jobs.length
        const applied = jobs.filter(job => job.applied).length
        const pending = total - applied

        return { total, applied, pending }
    }

    const stats = getStatsDisplay()

    return (
        <div className="container mx-auto px-4 py-8">
            <div className="space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight">Jobs</h1>
                        <p className="text-muted-foreground">
                            Manage all your job applications and opportunities
                        </p>
                    </div>
                    <Button onClick={refreshJobs} variant="outline" size="sm">
                        <RefreshCwIcon className="h-4 w-4 mr-2" />
                        Refresh
                    </Button>
                </div>

                {/* Stats Cards */}
                <div className="grid gap-4 md:grid-cols-3">
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Total Jobs</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">{stats.total}</div>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Applied</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-green-600">{stats.applied}</div>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">Pending</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-orange-600">{stats.pending}</div>
                        </CardContent>
                    </Card>
                </div>

                {/* Filters */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <FilterIcon className="h-5 w-5" />
                            Filters
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Job Title</label>
                                <Input
                                    placeholder="Filter by title..."
                                    value={filters.title || ''}
                                    onChange={(e) => handleFilterChange('title', e.target.value)}
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Company</label>
                                <Input
                                    placeholder="Filter by company..."
                                    value={filters.company || ''}
                                    onChange={(e) => handleFilterChange('company', e.target.value)}
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Location</label>
                                <Input
                                    placeholder="Filter by location..."
                                    value={filters.location || ''}
                                    onChange={(e) => handleFilterChange('location', e.target.value)}
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Application Status</label>
                                <Select
                                    value={filters.applicationStatus}
                                    onValueChange={(value) => handleFilterChange('applicationStatus', value)}
                                >
                                    <SelectTrigger>
                                        <SelectValue placeholder="All jobs" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="all">All Jobs</SelectItem>
                                        <SelectItem value="applied">Applied</SelectItem>
                                        <SelectItem value="not-applied">Not Applied</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Sort By</label>
                                <Select
                                    value={filters.sortBy}
                                    onValueChange={(value) => handleFilterChange('sortBy', value)}
                                >
                                    <SelectTrigger>
                                        <SelectValue placeholder="Sort by" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="newest">Newest First</SelectItem>
                                        <SelectItem value="oldest">Oldest First</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Jobs Table */}
                <Card>
                    <CardHeader>
                        <CardTitle>Job Listings</CardTitle>
                        <CardDescription>
                            {loading ? "Loading jobs..." : `Showing ${jobs.length} jobs`}
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="rounded-md border">
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Title</TableHead>
                                        <TableHead>Company</TableHead>
                                        <TableHead>Location</TableHead>
                                        <TableHead>Posted Date</TableHead>
                                        <TableHead>Type</TableHead>
                                        <TableHead>Status</TableHead>
                                        <TableHead>Applied</TableHead>
                                        <TableHead>Actions</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {loading ? (
                                        <TableRow>
                                            <TableCell colSpan={8} className="text-center py-8">
                                                <div className="flex items-center justify-center">
                                                    <RefreshCwIcon className="h-4 w-4 animate-spin mr-2" />
                                                    Loading jobs...
                                                </div>
                                            </TableCell>
                                        </TableRow>
                                    ) : jobs.length === 0 ? (
                                        <TableRow>
                                            <TableCell colSpan={8} className="text-center py-8">
                                                <div className="text-muted-foreground">
                                                    No jobs found matching your filters
                                                </div>
                                            </TableCell>
                                        </TableRow>
                                    ) : (
                                        jobs.map((job) => (
                                            <TableRow key={job.id}>
                                                <TableCell className="font-medium">{job.title}</TableCell>
                                                <TableCell>{job.company}</TableCell>
                                                <TableCell>{job.location}</TableCell>
                                                <TableCell>
                                                    <div className="flex items-center gap-1">
                                                        <CalendarIcon className="h-3 w-3 text-muted-foreground" />
                                                        {formatDate(job.postedAt)}
                                                    </div>
                                                </TableCell>
                                                <TableCell>{job.type}</TableCell>
                                                <TableCell>
                                                    <Badge variant={job.applied ? "default" : "secondary"}>
                                                        {job.applied ? "Applied" : "Pending"}
                                                    </Badge>
                                                </TableCell>
                                                <TableCell>
                                                    <Checkbox
                                                        checked={job.applied}
                                                        onCheckedChange={(checked) => handleStatusChange(job.id, checked as boolean)}
                                                    />
                                                </TableCell>
                                                <TableCell>
                                                    <Button
                                                        variant="outline"
                                                        size="sm"
                                                        onClick={() => job.url && window.open(job.url, '_blank')}
                                                        disabled={!job.url}
                                                    >
                                                        View Job
                                                    </Button>
                                                </TableCell>
                                            </TableRow>
                                        ))
                                    )}
                                </TableBody>
                            </Table>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
} 