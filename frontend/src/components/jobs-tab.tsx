"use client"

import { useEffect, useState } from "react"
import { fetchJobs, updateJobStatus } from "@/app/lib/api"
import type { Job, JobFilters } from "@/app/types/job"
import { useDashboard } from "@/app/contexts/dashboard-context"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { useToast } from "@/components/ui/use-toast"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"
import { format, isValid, parseISO } from "date-fns"
import { AppliedJobsList } from "./applied-jobs-list"
import { Building, Search, TrendingUp } from "lucide-react"

// Job interface imported from types/job.ts

function formatDate(dateString: string): string {
    try {
        const date = parseISO(dateString)
        if (!isValid(date)) {
            return 'Invalid date'
        }
        return format(date, 'MMM d, yyyy') // Changed format to show only date
    } catch (error) {
        console.error('Error formatting date:', error)
        return 'Invalid date'
    }
}

export function JobsTab() {
    const [jobs, setJobs] = useState<Job[]>([])
    const [loading, setLoading] = useState(true)
    const [filters, setFilters] = useState<JobFilters>({
        sortBy: 'newest'
    })
    const { toast } = useToast()
    const { updateJobApplication, refreshAppliedJobs } = useDashboard()

    useEffect(() => {
        const loadJobs = async () => {
            try {
                // For dashboard, we want only unapplied jobs, sorted by newest
                const dashboardFilters = {
                    ...filters,
                    sortBy: 'newest' as const
                }
                const data = await fetchJobs(dashboardFilters)

                // Filter to show only unapplied jobs and limit to recent ones
                const unappliedJobs = data
                    .filter((job: Job) => !job.applied)
                    .slice(0, 20) // Limit to 20 most recent unapplied jobs

                setJobs(unappliedJobs)
            } catch (error) {
                console.error('Failed to fetch jobs:', error)
            } finally {
                setLoading(false)
            }
        }
        loadJobs()
    }, [filters])

    const handleFilterChange = (key: keyof JobFilters, value: string) => {
        setFilters(prev => ({ ...prev, [key]: value }))
    }

    const handleStatusChange = async (jobId: string, applied: boolean) => {
        try {
            await updateJobStatus(jobId, applied)
            setJobs(jobs.map(job =>
                job.id === jobId ? { ...job, applied } : job
            ))

            // Update dashboard context
            updateJobApplication(jobId, applied)

            // If job was marked as applied, refresh the applied jobs list
            if (applied) {
                refreshAppliedJobs()
            }

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

    return (
        <div className="space-y-6">
            <div>
                <h3 className="text-lg font-medium">Job Management</h3>
                <p className="text-sm text-muted-foreground">
                    Track your applied jobs and discover new opportunities.
                </p>
            </div>

            <Tabs defaultValue="applied" className="space-y-4">
                <TabsList>
                    <TabsTrigger value="applied" className="flex items-center gap-2">
                        <Building className="h-4 w-4" />
                        Applied Jobs
                    </TabsTrigger>
                    <TabsTrigger value="available" className="flex items-center gap-2">
                        <Search className="h-4 w-4" />
                        Available Jobs
                    </TabsTrigger>
                </TabsList>

                <TabsContent value="applied">
                    <AppliedJobsList userId="demo_user" limit={15} />
                </TabsContent>

                <TabsContent value="available">
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <TrendingUp className="h-5 w-5" />
                                Available Job Opportunities
                            </CardTitle>
                            <CardDescription>
                                Browse and apply to job opportunities from our RSS feeds and other sources.
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-4">
                                        <Input
                                            placeholder="Filter by title..."
                                            className="max-w-sm"
                                            value={filters.title || ''}
                                            onChange={(e) => handleFilterChange('title', e.target.value)}
                                        />
                                        <Input
                                            placeholder="Filter by company..."
                                            className="max-w-sm"
                                            value={filters.company || ''}
                                            onChange={(e) => handleFilterChange('company', e.target.value)}
                                        />
                                    </div>
                                    <Button
                                        variant="outline"
                                        onClick={() => window.open('/jobs', '_blank')}
                                    >
                                        View All Jobs
                                    </Button>
                                </div>

                                <Table>
                                    <TableHeader>
                                        <TableRow>
                                            <TableHead>Title</TableHead>
                                            <TableHead>Company</TableHead>
                                            <TableHead>Location</TableHead>
                                            <TableHead>Posted Date</TableHead>
                                            <TableHead>Type</TableHead>
                                            <TableHead>Applied</TableHead>
                                            <TableHead>Action</TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        {loading ? (
                                            <TableRow>
                                                <TableCell colSpan={7} className="text-center">
                                                    Loading...
                                                </TableCell>
                                            </TableRow>
                                        ) : jobs.length === 0 ? (
                                            <TableRow>
                                                <TableCell colSpan={7} className="text-center">
                                                    No jobs found
                                                </TableCell>
                                            </TableRow>
                                        ) : (
                                            jobs.map((job) => (
                                                <TableRow key={job.id}>
                                                    <TableCell className="font-medium">{job.title}</TableCell>
                                                    <TableCell>{job.company}</TableCell>
                                                    <TableCell>{job.location}</TableCell>
                                                    <TableCell>{formatDate(job.postedAt)}</TableCell>
                                                    <TableCell>{job.type}</TableCell>
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
                                                        >
                                                            View
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
                </TabsContent>
            </Tabs>
        </div>
    )
} 