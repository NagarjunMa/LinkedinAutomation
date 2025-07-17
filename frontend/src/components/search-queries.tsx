"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { useToast } from "@/components/ui/use-toast"

interface SearchQuery {
    id: string
    title: string
    location: string
    jobType: string
    experienceLevel: string
    keywords: string[]
    createdAt: string
    isActive: boolean
}

export function SearchQueries() {
    const [queries, setQueries] = useState<SearchQuery[]>([])
    const [loading, setLoading] = useState(true)
    const { toast } = useToast()

    useEffect(() => {
        loadQueries()
    }, [])

    const loadQueries = async () => {
        try {
            const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
            const response = await fetch(`${API_URL}/api/v1/search/queries/`)
            if (!response.ok) {
                throw new Error("Failed to fetch search queries")
            }
            const data = await response.json()
            setQueries(data)
        } catch (error) {
            console.error("Error loading queries:", error)
            toast({
                title: "Error",
                description: "Failed to load search queries",
                variant: "destructive",
            })
        } finally {
            setLoading(false)
        }
    }

    const toggleQueryStatus = async (queryId: string, currentStatus: boolean) => {
        try {
            const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
            const response = await fetch(`${API_URL}/api/v1/search/queries/${queryId}/toggle/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ is_active: !currentStatus }),
            })

            if (!response.ok) {
                throw new Error("Failed to update query status")
            }

            // Update local state
            setQueries(queries.map(query =>
                query.id === queryId
                    ? { ...query, isActive: !currentStatus }
                    : query
            ))

            toast({
                title: "Success",
                description: `Search query ${currentStatus ? "paused" : "activated"}`,
            })
        } catch (error) {
            console.error("Error toggling query status:", error)
            toast({
                title: "Error",
                description: "Failed to update query status",
                variant: "destructive",
            })
        }
    }

    const deleteQuery = async (queryId: string) => {
        try {
            const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
            const response = await fetch(`${API_URL}/api/v1/search/queries/${queryId}/`, {
                method: "DELETE",
            })

            if (!response.ok) {
                throw new Error("Failed to delete query")
            }

            // Remove from local state
            setQueries(queries.filter(query => query.id !== queryId))

            toast({
                title: "Success",
                description: "Search query deleted",
            })
        } catch (error) {
            console.error("Error deleting query:", error)
            toast({
                title: "Error",
                description: "Failed to delete query",
                variant: "destructive",
            })
        }
    }

    if (loading) {
        return <div>Loading...</div>
    }

    return (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {queries.map((query) => (
                <Card key={query.id}>
                    <CardHeader>
                        <CardTitle className="flex items-center justify-between">
                            <span className="truncate">{query.title}</span>
                            <Badge variant={query.isActive ? "default" : "secondary"}>
                                {query.isActive ? "Active" : "Paused"}
                            </Badge>
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-2">
                            <div>
                                <span className="font-medium">Location:</span> {query.location || "Any"}
                            </div>
                            <div>
                                <span className="font-medium">Job Type:</span> {query.jobType || "Any"}
                            </div>
                            <div>
                                <span className="font-medium">Experience:</span>{" "}
                                {query.experienceLevel || "Any"}
                            </div>
                            <div>
                                <span className="font-medium">Keywords:</span>{" "}
                                {query.keywords?.length > 0
                                    ? query.keywords.join(", ")
                                    : "None"}
                            </div>
                            <div className="pt-4 flex justify-between">
                                <Button
                                    variant="outline"
                                    onClick={() => toggleQueryStatus(query.id, query.isActive)}
                                >
                                    {query.isActive ? "Pause" : "Activate"}
                                </Button>
                                <Button
                                    variant="destructive"
                                    onClick={() => deleteQuery(query.id)}
                                >
                                    Delete
                                </Button>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            ))}
        </div>
    )
} 