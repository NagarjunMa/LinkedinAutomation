"use client";
import React from 'react';
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { Button } from "./ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card"
import { Plus, Trash2, Clock } from "lucide-react"
import { useToast } from "./ui/use-toast"
import { format } from "date-fns"
import { Heading } from "@chakra-ui/react"

type SearchQuery = {
    id: number
    title: string
    location: string
    jobType: string
    experienceLevel: string
    schedule: string
    lastRun: string
}

async function fetchSearchQueries() {
    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const response = await fetch(`${API_URL}/api/v1/search/`)
    if (!response.ok) {
        throw new Error("Failed to fetch search queries")
    }
    return response.json()
}

async function deleteSearchQuery(id: number) {
    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const response = await fetch(`${API_URL}/api/v1/search/${id}/`, {
        method: "DELETE",
    })
    if (!response.ok) {
        throw new Error("Failed to delete search query")
    }
}

async function executeSearchQuery(id: number) {
    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const response = await fetch(`${API_URL}/api/v1/search/${id}/execute/`, {
        method: "POST",
    })
    if (!response.ok) {
        throw new Error("Failed to execute search query")
    }
    return response.json()
}

export const SearchQueries: React.FC = () => {
    const { toast } = useToast()
    const queryClient = useQueryClient()

    const { data: queries, isLoading } = useQuery<SearchQuery[]>({
        queryKey: ["searchQueries"],
        queryFn: fetchSearchQueries,
    })

    const deleteMutation = useMutation({
        mutationFn: deleteSearchQuery,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["searchQueries"] })
            toast({
                title: "Success",
                description: "Search query deleted",
            })
        },
        onError: () => {
            toast({
                title: "Error",
                description: "Failed to delete search query",
                variant: "destructive",
            })
        },
    })

    const executeMutation = useMutation({
        mutationFn: executeSearchQuery,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["jobs"] })
            toast({
                title: "Success",
                description: "Search query executed",
            })
        },
        onError: () => {
            toast({
                title: "Error",
                description: "Failed to execute search query",
                variant: "destructive",
            })
        },
    })

    if (isLoading) {
        return <div>Loading saved searches...</div>
    }

    return (
        <div>
            <Heading as="h2" size="6xl" mb={8} textAlign="center">Saved Searches</Heading>
            <Card className='justify-center items-center'>
                <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                        <span>Saved Searches</span>
                        <Button variant="outline" size="sm">
                            <Plus className="w-4 h-4 mr-2" />
                            New Search
                        </Button>
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        {queries?.map((query) => (
                            <div
                                key={query.id}
                                className="flex items-center justify-between p-4 border rounded-lg"
                            >
                                <div>
                                    <h3 className="font-medium">{query.title}</h3>
                                    <p className="text-sm text-muted-foreground">
                                        {query.location}
                                    </p>
                                    {query.lastRun && (
                                        <p className="text-xs text-muted-foreground mt-1">
                                            Last run: {format(new Date(query.lastRun), "MMM d, yyyy")}
                                        </p>
                                    )}
                                </div>
                                <div className="flex items-center space-x-2">
                                    {query.schedule && (
                                        <Button
                                            variant="ghost"
                                            size="sm"
                                            onClick={() => executeMutation.mutate(query.id)}
                                        >
                                            <Clock className="w-4 h-4" />
                                        </Button>
                                    )}
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => deleteMutation.mutate(query.id)}
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </Button>
                                </div>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>
        </div>

    )
} 