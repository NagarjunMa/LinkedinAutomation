import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import { Button } from "./ui/button"
import {
    Form,
    FormControl,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from "./ui/form"
import { Input } from "./ui/input"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "./ui/select"
import { useToast } from "./ui/use-toast"
import { useQueryClient } from "@tanstack/react-query"

const searchSchema = z.object({
    title: z.string().min(1, "Job title is required"),
    location: z.string().optional(),
    jobType: z.string().optional(),
    experienceLevel: z.string().optional(),
    keywords: z.string().optional(),
})

type SearchFormValues = z.infer<typeof searchSchema>

export function JobSearch() {
    const { toast } = useToast()
    const queryClient = useQueryClient()

    const form = useForm<SearchFormValues>({
        resolver: zodResolver(searchSchema),
        defaultValues: {
            title: "",
            location: "",
            jobType: "",
            experienceLevel: "",
            keywords: "",
        },
    })

    async function onSubmit(data: SearchFormValues) {
        try {
            const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
            const response = await fetch(`${API_URL}/api/v1/search/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(data),
            })

            if (!response.ok) {
                throw new Error("Failed to execute search")
            }

            const result = await response.json()

            // Invalidate and refetch jobs
            queryClient.invalidateQueries({ queryKey: ["jobs"] })

            toast({
                title: "Search executed",
                description: `Found ${result.length} jobs`,
            })
        } catch (error) {
            toast({
                title: "Error",
                description: "Failed to execute search",
                variant: "destructive",
            })
        }
    }

    return (
        <div className="bg-card rounded-lg p-6 shadow-sm">
            <h2 className="text-2xl font-semibold mb-4">Search Jobs</h2>

            <Form {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                    <FormField
                        control={form.control}
                        name="title"
                        render={({ field }) => (
                            <FormItem>
                                <FormLabel>Job Title</FormLabel>
                                <FormControl>
                                    <Input placeholder="e.g., Software Engineer" {...field} />
                                </FormControl>
                                <FormMessage />
                            </FormItem>
                        )}
                    />

                    <FormField
                        control={form.control}
                        name="location"
                        render={({ field }) => (
                            <FormItem>
                                <FormLabel>Location</FormLabel>
                                <FormControl>
                                    <Input placeholder="e.g., San Francisco, CA" {...field} />
                                </FormControl>
                                <FormMessage />
                            </FormItem>
                        )}
                    />

                    <div className="grid grid-cols-2 gap-4">
                        <FormField
                            control={form.control}
                            name="jobType"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Job Type</FormLabel>
                                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                                        <FormControl>
                                            <SelectTrigger>
                                                <SelectValue placeholder="Select job type" />
                                            </SelectTrigger>
                                        </FormControl>
                                        <SelectContent>
                                            <SelectItem value="full-time">Full Time</SelectItem>
                                            <SelectItem value="part-time">Part Time</SelectItem>
                                            <SelectItem value="contract">Contract</SelectItem>
                                            <SelectItem value="internship">Internship</SelectItem>
                                        </SelectContent>
                                    </Select>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />

                        <FormField
                            control={form.control}
                            name="experienceLevel"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Experience Level</FormLabel>
                                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                                        <FormControl>
                                            <SelectTrigger>
                                                <SelectValue placeholder="Select level" />
                                            </SelectTrigger>
                                        </FormControl>
                                        <SelectContent>
                                            <SelectItem value="entry">Entry Level</SelectItem>
                                            <SelectItem value="mid">Mid Level</SelectItem>
                                            <SelectItem value="senior">Senior Level</SelectItem>
                                            <SelectItem value="lead">Lead</SelectItem>
                                        </SelectContent>
                                    </Select>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                    </div>

                    <FormField
                        control={form.control}
                        name="keywords"
                        render={({ field }) => (
                            <FormItem>
                                <FormLabel>Keywords</FormLabel>
                                <FormControl>
                                    <Input placeholder="e.g., React, Python, AWS" {...field} />
                                </FormControl>
                                <FormMessage />
                            </FormItem>
                        )}
                    />

                    <Button type="submit" className="w-full">
                        Search Jobs
                    </Button>
                </form>
            </Form>
        </div>
    )
} 