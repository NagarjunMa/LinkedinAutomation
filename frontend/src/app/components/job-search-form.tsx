"use client"

import { useState } from "react"
import { useQueryClient } from "@tanstack/react-query"
import { Button } from "./ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card"
import { Input } from "./ui/input"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "./ui/select"
import { Switch } from "./ui/switch"
import { Label } from "./ui/label"
import { useToast } from "./ui/use-toast"

type SearchParams = {
    keywords: string
    location: string
    jobType: string
    experienceLevel: string
    schedule: string
    remote: boolean
    postedWithin: string
}

const jobTypes = [
    "Full-time",
    "Part-time",
    "Contract",
    "Temporary",
    "Internship",
]

const experienceLevels = [
    "Entry Level",
    "Associate",
    "Mid-Senior Level",
    "Director",
    "Executive",
]

const schedules = [
    "Morning",
    "Afternoon",
    "Evening",
    "Night",
    "Weekend",
]

const postedWithinOptions = [
    "24 hours",
    "3 days",
    "1 week",
    "2 weeks",
    "1 month",
]

export function JobSearchForm() {
    const { toast } = useToast()
    const queryClient = useQueryClient()
    const [isLoading, setIsLoading] = useState(false)
    const [searchParams, setSearchParams] = useState<SearchParams>({
        keywords: "",
        location: "",
        jobType: "",
        experienceLevel: "",
        schedule: "",
        remote: false,
        postedWithin: "",
    })

    async function handleSearch(e: React.FormEvent) {
        console.log("handleSearch function called");
        console.log("searchParams", searchParams);
        e.preventDefault()
        setIsLoading(true)

        try {
            const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
            console.log("API_URL", API_URL);
            const response = await fetch(`${API_URL}/api/v1/search/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(searchParams),
            })

            if (!response.ok) {
                throw new Error("Search failed")
            }

            await queryClient.invalidateQueries({ queryKey: ["jobs"] })
            toast({
                title: "Success",
                description: "Search completed successfully",
            })
        } catch (error) {
            toast({
                title: "Error",
                description: "Failed to perform search",
                variant: "destructive",
            })
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <Card>
            <CardHeader>
                <CardTitle>Search Jobs</CardTitle>
            </CardHeader>
            <CardContent>
                <form onSubmit={handleSearch} className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label htmlFor="keywords">Keywords</Label>
                            <Input
                                id="keywords"
                                placeholder="Job title, skills, or company"
                                value={searchParams.keywords}
                                onChange={(e) =>
                                    setSearchParams({ ...searchParams, keywords: e.target.value })
                                }
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="location">Location</Label>
                            <Input
                                id="location"
                                placeholder="City, state, or remote"
                                value={searchParams.location}
                                onChange={(e) =>
                                    setSearchParams({ ...searchParams, location: e.target.value })
                                }
                            />
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="space-y-2">
                            <Label htmlFor="jobType">Job Type</Label>
                            <Select
                                value={searchParams.jobType}
                                onValueChange={(value) =>
                                    setSearchParams({ ...searchParams, jobType: value })
                                }
                            >
                                <SelectTrigger>
                                    <SelectValue placeholder="Select job type" />
                                </SelectTrigger>
                                <SelectContent>
                                    {jobTypes.map((type) => (
                                        <SelectItem key={type} value={type}>
                                            {type}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="experienceLevel">Experience Level</Label>
                            <Select
                                value={searchParams.experienceLevel}
                                onValueChange={(value) =>
                                    setSearchParams({ ...searchParams, experienceLevel: value })
                                }
                            >
                                <SelectTrigger>
                                    <SelectValue placeholder="Select experience level" />
                                </SelectTrigger>
                                <SelectContent>
                                    {experienceLevels.map((level) => (
                                        <SelectItem key={level} value={level}>
                                            {level}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="schedule">Schedule</Label>
                            <Select
                                value={searchParams.schedule}
                                onValueChange={(value) =>
                                    setSearchParams({ ...searchParams, schedule: value })
                                }
                            >
                                <SelectTrigger>
                                    <SelectValue placeholder="Select schedule" />
                                </SelectTrigger>
                                <SelectContent>
                                    {schedules.map((schedule) => (
                                        <SelectItem key={schedule} value={schedule}>
                                            {schedule}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label htmlFor="postedWithin">Posted Within</Label>
                            <Select
                                value={searchParams.postedWithin}
                                onValueChange={(value) =>
                                    setSearchParams({ ...searchParams, postedWithin: value })
                                }
                            >
                                <SelectTrigger>
                                    <SelectValue placeholder="Select time range" />
                                </SelectTrigger>
                                <SelectContent>
                                    {postedWithinOptions.map((option) => (
                                        <SelectItem key={option} value={option}>
                                            {option}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>

                        <div className="flex items-center space-x-2">
                            <Switch
                                id="remote"
                                checked={searchParams.remote}
                                onCheckedChange={(checked) =>
                                    setSearchParams({ ...searchParams, remote: checked })
                                }
                            />
                            <Label htmlFor="remote">Remote Only</Label>
                        </div>
                    </div>

                    <Button type="submit" className="w-full" disabled={isLoading}>
                        {isLoading ? "Searching..." : "Search Jobs"}
                    </Button>
                </form>
            </CardContent>
        </Card>
    )
} 