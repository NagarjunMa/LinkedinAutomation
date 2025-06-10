"use client";

import React from 'react';
import { useQuery } from "@tanstack/react-query"
import { Button } from "./ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card"
import { Badge } from "./ui/badge"
import { ExternalLink, Bookmark, Share2 } from "lucide-react"
import { format } from "date-fns"
import { fetchJobs } from '../lib/api'

type Job = {
    id: number
    title: string
    company: string
    location: string
    type: string
    description: string
    url: string
    postedAt: string
    salary?: string
    experience?: string
    skills?: string[]
}

export function JobList() {
    const { data: jobs, isLoading } = useQuery<Job[]>({
        queryKey: ["jobs"],
        queryFn: fetchJobs,
    })

    if (isLoading) {
        return <div>Loading jobs...</div>
    }

    return (
        <Card>
            <CardHeader>
                <CardTitle>Job Listings</CardTitle>
            </CardHeader>
            <CardContent>
                <div className="space-y-4">
                    {jobs?.map((job) => (
                        <div
                            key={job.id}
                            className="p-4 border rounded-lg hover:bg-accent/50 transition-colors"
                        >
                            <div className="flex items-start justify-between">
                                <div>
                                    <h3 className="font-medium text-lg">{job.title}</h3>
                                    <p className="text-sm text-muted-foreground">{job.company}</p>
                                    <div className="flex items-center gap-2 mt-2">
                                        <Badge variant="secondary">{job.type}</Badge>
                                        <Badge variant="outline">{job.location}</Badge>
                                        {job.salary && (
                                            <Badge variant="outline">{job.salary}</Badge>
                                        )}
                                    </div>
                                    {job.skills && job.skills.length > 0 && (
                                        <div className="flex flex-wrap gap-2 mt-2">
                                            {job.skills.map((skill) => (
                                                <Badge key={skill} variant="secondary">
                                                    {skill}
                                                </Badge>
                                            ))}
                                        </div>
                                    )}
                                    <p className="text-sm text-muted-foreground mt-2">
                                        {job.postedAt && !isNaN(new Date(job.postedAt).getTime())
                                            ? `Posted ${format(new Date(job.postedAt), "MMM d, yyyy")}`
                                            : "Posted date unknown"}
                                    </p>
                                </div>
                                <div className="flex items-center space-x-2">
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => window.open(job.url, "_blank")}
                                    >
                                        <ExternalLink className="w-4 h-4" />
                                    </Button>
                                    <Button variant="ghost" size="sm">
                                        <Bookmark className="w-4 h-4" />
                                    </Button>
                                    <Button variant="ghost" size="sm">
                                        <Share2 className="w-4 h-4" />
                                    </Button>
                                </div>
                            </div>
                            <p className="text-sm mt-4 line-clamp-3">{job.description}</p>
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    )
} 