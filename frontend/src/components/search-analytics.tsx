"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { useToast } from "@/components/ui/use-toast"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
    AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import { format, parseISO } from "date-fns"
import { SearchIcon, TrendingUpIcon, PlayIcon, PauseIcon, TrashIcon, EditIcon, PlusIcon } from "lucide-react"

interface SearchQuery {
    id: string
    title: string
    location: string
    jobType: string
    experienceLevel: string
    keywords: string[]
    createdAt: string
    lastRun?: string
    isActive: boolean
    resultsCount: number
    applicationsCount: number
    successRate: number
}

export function SearchAnalytics() {
    const [queries, setQueries] = useState<SearchQuery[]>([])
    const [loading, setLoading] = useState(true)
    const [filter, setFilter] = useState<'all' | 'active' | 'inactive'>('all')
    const [searchTerm, setSearchTerm] = useState('')
    const { toast } = useToast()

    useEffect(() => {
        const loadSearchQueries = async () => {
            try {
                setLoading(true)
                const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
                
                // Fetch basic search queries
                const response = await fetch(`${API_URL}/api/v1/search/queries/`)
                if (!response.ok) {
                    throw new Error("Failed to fetch search queries")
                }
                const basicQueries = await response.json()
                
                // Transform basic queries to include analytics data
                // In a real implementation, this would be a separate API call
                const queriesWithAnalytics: SearchQuery[] = basicQueries.map((query: any, index: number) => ({
                    ...query,
                    lastRun: query.lastRun || (index % 2 === 0 ? new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString() : undefined),
                    resultsCount: Math.floor(Math.random() * 50) + 10, // Mock data
                    applicationsCount: Math.floor(Math.random() * 15) + 1, // Mock data
                    successRate: Number((Math.random() * 30 + 10).toFixed(1)) // Mock data
                }))
                
                setQueries(queriesWithAnalytics)
            } catch (error) {
                console.error('Failed to fetch search queries:', error)
                
                // Fallback to mock data if API fails
                const mockData: SearchQuery[] = [
                    {
                        id: '1',
                        title: 'Senior Software Engineer',
                        location: 'San Francisco, CA',
                        jobType: 'Full-time',
                        experienceLevel: 'Senior',
                        keywords: ['React', 'Node.js', 'TypeScript'],
                        createdAt: '2024-01-15T10:00:00Z',
                        lastRun: '2024-01-20T08:30:00Z',
                        isActive: true,
                        resultsCount: 45,
                        applicationsCount: 12,
                        successRate: 26.7
                    },
                    {
                        id: '2',
                        title: 'Frontend Developer',
                        location: 'Remote',
                        jobType: 'Full-time',
                        experienceLevel: 'Mid-level',
                        keywords: ['Vue.js', 'JavaScript', 'CSS'],
                        createdAt: '2024-01-10T14:00:00Z',
                        lastRun: '2024-01-19T09:15:00Z',
                        isActive: true,
                        resultsCount: 32,
                        applicationsCount: 8,
                        successRate: 25.0
                    }
                ]
                setQueries(mockData)
                
                toast({
                    title: "Warning",
                    description: "Using mock data - API unavailable",
                    variant: "destructive",
                })
            } finally {
                setLoading(false)
            }
        }

        loadSearchQueries()
    }, [toast])

    const filteredQueries = queries.filter(query => {
        const matchesFilter = filter === 'all' ||
            (filter === 'active' && query.isActive) ||
            (filter === 'inactive' && !query.isActive)

        const matchesSearch = searchTerm === '' ||
            query.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
            query.location.toLowerCase().includes(searchTerm.toLowerCase()) ||
            query.keywords.some(keyword => keyword.toLowerCase().includes(searchTerm.toLowerCase()))

        return matchesFilter && matchesSearch
    })

        const toggleQueryStatus = async (queryId: string) => {
        try {
            const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
            const query = queries.find(q => q.id === queryId)
            const newStatus = !query?.isActive
            
            const response = await fetch(`${API_URL}/api/v1/search/queries/${queryId}/toggle`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ isActive: newStatus }),
            })

            if (!response.ok) {
                throw new Error('Failed to update query status')
            }

            // Update local state
            setQueries(queries.map(q => 
                q.id === queryId 
                    ? { ...q, isActive: newStatus }
                    : q
            ))
            
            toast({
                title: "Success",
                description: `Search query ${newStatus ? 'activated' : 'paused'}`,
            })
        } catch (error) {
            console.error('Error toggling query status:', error)
            toast({
                title: "Error",
                description: "Failed to update search query",
                variant: "destructive",
            })
        }
    }

    const deleteQuery = async (queryId: string) => {
        try {
            const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
            
            const response = await fetch(`${API_URL}/api/v1/search/queries/${queryId}`, {
                method: 'DELETE',
            })

            if (!response.ok) {
                throw new Error('Failed to delete query')
            }

            // Update local state
            setQueries(queries.filter(query => query.id !== queryId))
            toast({
                title: "Success",
                description: "Search query deleted successfully",
            })
        } catch (error) {
            console.error('Error deleting query:', error)
            toast({
                title: "Error",
                description: "Failed to delete search query",
                variant: "destructive",
            })
        }
    }

        const runQuery = async (queryId: string) => {
        try {
            const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
            
            const response = await fetch(`${API_URL}/api/v1/search/queries/${queryId}/run`, {
                method: 'POST',
            })

            if (!response.ok) {
                throw new Error('Failed to run search query')
            }

            toast({
                title: "Search Started",
                description: "Search query is now running...",
            })
            
            // Update last run time
            setQueries(queries.map(query => 
                query.id === queryId 
                    ? { ...query, lastRun: new Date().toISOString() }
                    : query
            ))
        } catch (error) {
            console.error('Error running query:', error)
            toast({
                title: "Error",
                description: "Failed to run search query",
                variant: "destructive",
            })
        }
    }

    const getStats = () => {
        const totalQueries = queries.length
        const activeQueries = queries.filter(q => q.isActive).length
        const totalResults = queries.reduce((sum, q) => sum + q.resultsCount, 0)
        const totalApplications = queries.reduce((sum, q) => sum + q.applicationsCount, 0)
        const averageSuccessRate = queries.length > 0
            ? queries.reduce((sum, q) => sum + q.successRate, 0) / queries.length
            : 0

        return { totalQueries, activeQueries, totalResults, totalApplications, averageSuccessRate }
    }

    const stats = getStats()

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h3 className="text-lg font-medium">Search Query Analytics</h3>
                    <p className="text-sm text-muted-foreground">
                        Manage and analyze your automated job search queries
                    </p>
                </div>
                <Button>
                    <PlusIcon className="h-4 w-4 mr-2" />
                    New Search Query
                </Button>
            </div>

            {/* Stats Cards */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Total Queries</CardTitle>
                        <SearchIcon className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{stats.totalQueries}</div>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Active Queries</CardTitle>
                        <PlayIcon className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-green-600">{stats.activeQueries}</div>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Total Results</CardTitle>
                        <TrendingUpIcon className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{stats.totalResults}</div>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Applications</CardTitle>
                        <TrendingUpIcon className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{stats.totalApplications}</div>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Avg Success Rate</CardTitle>
                        <TrendingUpIcon className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{stats.averageSuccessRate.toFixed(1)}%</div>
                    </CardContent>
                </Card>
            </div>

            {/* Filters */}
            <div className="flex items-center gap-4">
                <Input
                    placeholder="Search queries..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="max-w-sm"
                />
                <Select value={filter} onValueChange={(value: 'all' | 'active' | 'inactive') => setFilter(value)}>
                    <SelectTrigger className="w-[180px]">
                        <SelectValue placeholder="Filter by status" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="all">All Queries</SelectItem>
                        <SelectItem value="active">Active</SelectItem>
                        <SelectItem value="inactive">Inactive</SelectItem>
                    </SelectContent>
                </Select>
            </div>

            {/* Search Queries Table */}
            <Card>
                <CardHeader>
                    <CardTitle>Search Queries</CardTitle>
                    <CardDescription>
                        {loading ? "Loading..." : `${filteredQueries.length} search queries`}
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="rounded-md border">
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Query</TableHead>
                                    <TableHead>Location</TableHead>
                                    <TableHead>Keywords</TableHead>
                                    <TableHead>Status</TableHead>
                                    <TableHead>Results</TableHead>
                                    <TableHead>Applications</TableHead>
                                    <TableHead>Success Rate</TableHead>
                                    <TableHead>Last Run</TableHead>
                                    <TableHead>Actions</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {loading ? (
                                    <TableRow>
                                        <TableCell colSpan={9} className="text-center py-8">
                                            Loading search queries...
                                        </TableCell>
                                    </TableRow>
                                ) : filteredQueries.length === 0 ? (
                                    <TableRow>
                                        <TableCell colSpan={9} className="text-center py-8">
                                            <div className="text-muted-foreground">
                                                No search queries found
                                            </div>
                                        </TableCell>
                                    </TableRow>
                                ) : (
                                    filteredQueries.map((query) => (
                                        <TableRow key={query.id}>
                                            <TableCell>
                                                <div>
                                                    <div className="font-medium">{query.title}</div>
                                                    <div className="text-sm text-muted-foreground">
                                                        {query.jobType} · {query.experienceLevel}
                                                    </div>
                                                </div>
                                            </TableCell>
                                            <TableCell>{query.location}</TableCell>
                                            <TableCell>
                                                <div className="flex flex-wrap gap-1">
                                                    {query.keywords.slice(0, 2).map((keyword, index) => (
                                                        <Badge key={index} variant="outline" className="text-xs">
                                                            {keyword}
                                                        </Badge>
                                                    ))}
                                                    {query.keywords.length > 2 && (
                                                        <Badge variant="outline" className="text-xs">
                                                            +{query.keywords.length - 2}
                                                        </Badge>
                                                    )}
                                                </div>
                                            </TableCell>
                                            <TableCell>
                                                <Badge variant={query.isActive ? "default" : "secondary"}>
                                                    {query.isActive ? "Active" : "Paused"}
                                                </Badge>
                                            </TableCell>
                                            <TableCell>{query.resultsCount}</TableCell>
                                            <TableCell>{query.applicationsCount}</TableCell>
                                            <TableCell>{query.successRate.toFixed(1)}%</TableCell>
                                            <TableCell>
                                                {query.lastRun ? format(parseISO(query.lastRun), 'MMM dd, HH:mm') : 'Never'}
                                            </TableCell>
                                            <TableCell>
                                                <div className="flex items-center gap-2">
                                                    <Button
                                                        variant="outline"
                                                        size="sm"
                                                        onClick={() => runQuery(query.id)}
                                                    >
                                                        <PlayIcon className="h-3 w-3" />
                                                    </Button>
                                                    <Button
                                                        variant="outline"
                                                        size="sm"
                                                        onClick={() => toggleQueryStatus(query.id)}
                                                    >
                                                        {query.isActive ? (
                                                            <PauseIcon className="h-3 w-3" />
                                                        ) : (
                                                            <PlayIcon className="h-3 w-3" />
                                                        )}
                                                    </Button>
                                                    <Button
                                                        variant="outline"
                                                        size="sm"
                                                    >
                                                        <EditIcon className="h-3 w-3" />
                                                    </Button>
                                                    <AlertDialog>
                                                        <AlertDialogTrigger asChild>
                                                            <Button
                                                                variant="outline"
                                                                size="sm"
                                                            >
                                                                <TrashIcon className="h-3 w-3" />
                                                            </Button>
                                                        </AlertDialogTrigger>
                                                        <AlertDialogContent>
                                                            <AlertDialogHeader>
                                                                <AlertDialogTitle>Delete Search Query</AlertDialogTitle>
                                                                <AlertDialogDescription>
                                                                    Are you sure you want to delete this search query? This action cannot be undone.
                                                                </AlertDialogDescription>
                                                            </AlertDialogHeader>
                                                            <AlertDialogFooter>
                                                                <AlertDialogCancel>Cancel</AlertDialogCancel>
                                                                <AlertDialogAction onClick={() => deleteQuery(query.id)}>
                                                                    Delete
                                                                </AlertDialogAction>
                                                            </AlertDialogFooter>
                                                        </AlertDialogContent>
                                                    </AlertDialog>
                                                </div>
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
    )
} 